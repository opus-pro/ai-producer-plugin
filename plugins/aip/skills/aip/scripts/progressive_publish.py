"""Publish one completed effect at a time without asking a model to drive MCP."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import mimetypes
from pathlib import Path
import re
import shutil
import tempfile
import time

from preflight import check
from publication_guard import inspect_index, validate_progress
import upload_batch

SIGN_BATCH_SIZE = 50
MAX_FILES = 200
TASK_WAIT_SECONDS = 45
STAGE_TIMEOUT_SECONDS = 900
UNLOCK_ATTEMPTS = 5
# The service includes its own runtime files in a host-authored commit receipt.
SERVER_RUNTIME_PATHS = frozenset({
    "render-engine/package.json", "render-engine/public/vendor/gsap.min.js",
    "render-engine/public/vendor/fit-engine.js", "render-engine/public/vendor/connector-engine.js",
})


def relative_path(value):
    if not isinstance(value, str):
        raise ValueError("invalid_publication_path")
    if value.startswith("render-engine/"):
        value = value[len("render-engine/"):]
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError("invalid_publication_path")
    return path.as_posix()


def upload_signed(root, rows):
    jobs = upload_batch.prepare(root, rows)
    with ThreadPoolExecutor(max_workers=upload_batch.MAX_WORKERS) as pool:
        results = list(pool.map(upload_batch.upload, jobs))
    if not all(item.get("ok") is True for item in results):
        raise RuntimeError("publication_upload_failed")


class ProgressPublisher:
    """One task-scoped publication session; transport owns host authentication.

    Construct after writing the full planned speaker/audio base, before adding any
    visual hosts. Author one effect, call publish, then author the next. A failure
    stops this session without replaying a mutation or adopting a concurrent edit.
    """

    def __init__(self, workspace, project_id, planned_duration, transport,
                 uploader=upload_signed, on_progress=None):
        self.root = Path(workspace).resolve(strict=True)
        self.project_id = project_id
        self.transport = transport
        self.uploader = uploader
        self.on_progress = on_progress or self._print_progress
        self.duration = float(planned_duration)
        if not math.isfinite(self.duration) or self.duration <= 0:
            raise ValueError("invalid_planned_duration")
        self.baseline = (self.root / "index.html").read_text(encoding="utf-8")
        base = inspect_index(self.baseline)
        if base["effects"] or not math.isclose(base["duration"], self.duration, abs_tol=1e-6):
            raise ValueError("full_timeline_base_required")
        self.previous = self.baseline
        self.digest = None
        self.remote = set()
        self.finished = False
        self.failed = False
        self.publications = 0

    @staticmethod
    def _print_progress(row):
        print(json.dumps(row, separators=(",", ":")), flush=True)

    def _call(self, tool, arguments):
        return self.transport.call(tool, arguments)

    def _listing(self):
        cursor = None
        seen = set()
        while True:
            args = {"project_id": self.project_id}
            if cursor:
                args["cursor"] = cursor
            page = self._call("list_workspace", args)
            digest = page.get("digest")
            if not isinstance(digest, str) or not digest:
                raise RuntimeError("workspace_digest_missing")
            if self.digest is not None and digest != self.digest:
                raise RuntimeError("workspace_changed_during_listing")
            self.digest = digest
            if page.get("staged"):
                raise RuntimeError("uncommitted_workspace_files_present")
            for entry in page.get("files", []):
                self.remote.add(relative_path(entry["path"]))
            cursor = page.get("next_cursor")
            if not cursor:
                return
            if cursor in seen:
                raise RuntimeError("workspace_cursor_repeated")
            seen.add(cursor)

    def _copy(self, relative, target):
        source = (self.root / relative).resolve(strict=True)
        if not source.is_relative_to(self.root) or not source.is_file():
            raise ValueError("publication_path_outside_workspace")
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        return destination

    def _snapshot(self, paths, target):
        # Include accepted local documents for static graph inspection. Confirmed
        # remote source media is referenced, never copied or uploaded again.
        for relative in self.remote.difference(paths):
            if Path(relative).suffix.lower() in {".html", ".css"} and (self.root / relative).is_file():
                self._copy(relative, target)
        manifest = []
        for relative in paths:
            file = self._copy(relative, target)
            manifest.append({"path": "render-engine/" + relative,
                             "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                             "content_type": mimetypes.guess_type(relative)[0] or "application/octet-stream"})
        result = check(target, self.remote)
        if not result["ok"]:
            codes = sorted({item["code"] for item in result["errors"]})
            raise ValueError("publication_preflight_failed:" + ",".join(codes))
        return manifest

    def _upload(self, snapshot, manifest):
        for offset in range(0, len(manifest), SIGN_BATCH_SIZE):
            batch = manifest[offset:offset + SIGN_BATCH_SIZE]
            result = self._call("sign_workspace_upload", {
                "project_id": self.project_id, "authoring": True,
                "files": [{"path": row["path"], "content_type": row["content_type"]} for row in batch],
            })
            uploads = result.get("uploads", [])
            requested = {relative_path(row["path"]) for row in batch}
            returned = [relative_path(row["path"]) for row in uploads]
            if result.get("rejected") or len(returned) != len(requested) or set(returned) != requested:
                raise RuntimeError("publication_signing_refused")
            self.uploader(snapshot, uploads)

    def _wait(self, task_id):
        deadline = time.monotonic() + STAGE_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            task = self._call("get_task", {"task_id": task_id, "wait_seconds": TASK_WAIT_SECONDS})
            if task.get("terminal") is True:
                if task.get("succeeded") is not True:
                    raise RuntimeError("publication_task_failed")
                result = task.get("result")
                if not isinstance(result, dict) or result.get("outcome") not in {"accepted", "accepted_with_warnings"}:
                    raise RuntimeError("publication_not_accepted")
                return result
        raise TimeoutError("publication_task_timeout")

    def _settled(self, final):
        for _ in range(UNLOCK_ATTEMPTS):
            project = self._call("get_project", {"project_id": self.project_id})
            if project.get("active_task_id") is None:
                if project.get("editable_ready") is not True:
                    raise RuntimeError("publication_preview_not_ready")
                lease = project.get("external_authoring")
                if "external_authoring" not in project or bool(lease) == final:
                    raise RuntimeError("publication_authoring_state_mismatch")
                return
            time.sleep(0.5)
        raise RuntimeError("publication_lock_not_released")

    def publish(self, files, *, final=False):
        if self.finished or self.failed:
            raise RuntimeError("publication_session_closed")
        try:
            paths = [relative_path(path) for path in files]
            if not paths or len(paths) > MAX_FILES or len(set(paths)) != len(paths) or "index.html" not in paths:
                raise ValueError("invalid_publication_files")
            candidate = (self.root / "index.html").read_text(encoding="utf-8")
            state = validate_progress(self.baseline, self.previous, candidate, self.duration)
            if self.digest is None:
                self._listing()
            with tempfile.TemporaryDirectory(prefix="aip-publication-") as directory:
                snapshot = Path(directory).resolve()
                manifest = self._snapshot(paths, snapshot)
                if (snapshot / "index.html").read_text(encoding="utf-8") != candidate:
                    raise RuntimeError("workspace_changed_during_snapshot")
                self._upload(snapshot, manifest)
                started = self._call("commit_workspace", {
                    "project_id": self.project_id, "authoring": not final, "base_digest": self.digest,
                    "expected_files": [{"path": row["path"], "sha256": row["sha256"]} for row in manifest],
                })
                task_id = started.get("task_id")
                if not isinstance(task_id, str) or not task_id:
                    raise RuntimeError("publication_task_missing")
                receipt = self._wait(task_id)
                accepted = receipt.get("accepted", [])
                expected = {row["path"] for row in manifest}
                if (not isinstance(accepted, list) or not all(isinstance(path, str) for path in accepted)
                        or not expected.issubset(accepted)
                        or set(accepted).difference(expected, SERVER_RUNTIME_PATHS)):
                    raise RuntimeError("publication_receipt_mismatch")
                digest = receipt.get("digest")
                if not isinstance(digest, str) or not digest:
                    raise RuntimeError("publication_receipt_digest_missing")
                self._settled(final)
            self.digest = digest
            self.previous = candidate
            self.remote.update(relative_path(path) for path in accepted)
            self.publications += 1
            self.finished = final
            report = {"published_effects": len(state["effects"]), "duration_seconds": state["duration"],
                      "task_id": task_id, "final": final, "host_model_turns": 0,
                      "warning_codes": sorted({str(row.get("rule", row.get("code", "service_warning")))
                                               for row in receipt.get("warnings", [])
                                               if isinstance(row, dict) and re.fullmatch(
                                                   r"[a-zA-Z0-9_-]{1,100}", str(row.get("rule", row.get("code", "service_warning"))))})}
            self.on_progress(report)
            return report
        except Exception:
            self.failed = True
            raise

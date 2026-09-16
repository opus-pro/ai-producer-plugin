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
from publication_guard import inspect_index, validate_checkpoint_progress
import upload_batch

SIGN_BATCH_SIZE = 50
MAX_FILES = 200
TASK_WAIT_SECONDS = 45
STAGE_TIMEOUT_SECONDS = 900
UNLOCK_ATTEMPTS = 5
MAX_ERROR_ISSUES = 3
MAX_REPAIR_HINT_CHARS = 300
# The service includes its own runtime files in a host-authored commit receipt.
SERVER_RUNTIME_PATHS = frozenset({
    "render-engine/package.json", "render-engine/public/vendor/gsap.min.js",
    "render-engine/public/vendor/fit-engine.js", "render-engine/public/vendor/connector-engine.js",
})
CHECKPOINT_SCHEMA = 1
CHECKPOINT_STATUSES = frozenset({"ready", "publishing", "failed", "finished"})


def relative_path(value):
    if not isinstance(value, str):
        raise ValueError("invalid_publication_path")
    if value.startswith("render-engine/"):
        value = value[len("render-engine/"):]
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError("invalid_publication_path")
    return path.as_posix()


def _safe_issue(value):
    if not isinstance(value, dict):
        return None
    issue = {}
    code = value.get("code", value.get("rule"))
    if isinstance(code, str) and re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", code):
        issue["code"] = code
    path = value.get("path")
    if isinstance(path, str) and path.startswith("render-engine/") and len(path) <= 512:
        try:
            relative = relative_path(path)
        except ValueError:
            relative = None
        if relative and all(re.fullmatch(r"[a-zA-Z0-9._-]+", part) for part in Path(relative).parts):
            issue["path"] = "render-engine/" + relative
    hint = value.get("repair_hint")
    if isinstance(hint, str):
        hint = " ".join(hint.split())
        if (hint and len(hint) <= MAX_REPAIR_HINT_CHARS and hint.isascii()
                and re.search(r"(?:[a-z][a-z0-9+.-]*:)?//", hint, re.IGNORECASE) is None):
            issue["repair_hint"] = hint
    return issue or None


def _publication_error(prefix, values):
    issues = []
    for value in values if isinstance(values, list) else []:
        issue = _safe_issue(value)
        if issue:
            issues.append(issue)
        if len(issues) == MAX_ERROR_ISSUES:
            break
    detail = ":" + json.dumps({"issues": issues}, separators=(",", ":")) if issues else ""
    return RuntimeError(prefix + detail)


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
        self.baseline_snapshot = base
        self.previous_effects = {}
        self.digest = None
        self.remote = set()
        self.accepted_hashes = {}
        self.finished = False
        self.failed = False
        self.publications = 0

    @classmethod
    def resume(cls, workspace, state, transport, uploader=upload_signed, on_progress=None):
        """Resume an accepted checkpoint without retaining prior HTML or credentials."""
        root = Path(workspace).resolve(strict=True)
        values = _validate_checkpoint_state(state, root)
        if values["status"] != "ready":
            raise RuntimeError("publication_checkpoint_closed")
        self = cls.__new__(cls)
        self.root = root
        self.project_id = values["project_id"]
        self.transport = transport
        self.uploader = uploader
        self.on_progress = on_progress or self._print_progress
        self.duration = values["planned_duration"]
        self.baseline = None
        self.previous = None
        self.baseline_snapshot = values["baseline"]
        self.previous_effects = values["effects"]
        self.digest = values["digest"]
        self.remote = set(values["remote"])
        self.accepted_hashes = values["accepted_hashes"]
        self.finished = False
        self.failed = False
        self.publications = values["publications"]
        return self

    def checkpoint(self, status=None):
        """Return the credential-free semantic state needed by the next process."""
        if status is None:
            status = "failed" if self.failed else "finished" if self.finished else "ready"
        if status not in CHECKPOINT_STATUSES:
            raise ValueError("invalid_checkpoint_status")
        if status == "failed" and not self.failed:
            raise ValueError("invalid_checkpoint_status")
        if status == "finished" and not self.finished:
            raise ValueError("invalid_checkpoint_status")
        if status in {"ready", "publishing"} and (self.failed or self.finished):
            raise ValueError("invalid_checkpoint_status")
        return {
            "schema": CHECKPOINT_SCHEMA,
            "status": status,
            "workspace": str(self.root),
            "project_id": self.project_id,
            "planned_duration": self.duration,
            "baseline": _json_snapshot(self.baseline_snapshot),
            "effects": self.previous_effects,
            "digest": self.digest,
            "remote": sorted(self.remote),
            "accepted_hashes": self.accepted_hashes,
            "publications": self.publications,
        }

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

    def _reject_unpublished_compositions(self, paths):
        allowed = set(paths).union(self.remote)
        ahead = []
        directory = self.root / "compositions"
        if directory.is_dir():
            for file in directory.rglob("*.html"):
                relative = file.relative_to(self.root).as_posix()
                if relative not in allowed:
                    ahead.append(relative)
        if ahead:
            raise ValueError("future_effect_files_present")

    def _verify_accepted_files(self):
        for relative, expected in self.accepted_hashes.items():
            if relative == "index.html":
                continue
            file = self.root / relative
            if file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest() != expected:
                raise ValueError("accepted_file_changed")

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
                raise _publication_error("publication_signing_refused", result.get("rejected"))
            self.uploader(snapshot, uploads)

    def _wait(self, task_id):
        deadline = time.monotonic() + STAGE_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            task = self._call("get_task", {"task_id": task_id, "wait_seconds": TASK_WAIT_SECONDS})
            if task.get("terminal") is True:
                result = task.get("result")
                if task.get("succeeded") is not True:
                    issues = result.get("issues") if isinstance(result, dict) else None
                    raise _publication_error("publication_task_failed", issues)
                if not isinstance(result, dict) or result.get("outcome") not in {"accepted", "accepted_with_warnings"}:
                    issues = result.get("issues") if isinstance(result, dict) else None
                    raise _publication_error("publication_not_accepted", issues)
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
            state = validate_checkpoint_progress(
                self.baseline_snapshot, self.previous_effects, candidate, self.duration,
            )
            if self.digest is None:
                self._listing()
            self._reject_unpublished_compositions(paths)
            self._verify_accepted_files()
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
            self.previous_effects = state["effects"]
            self.remote.update(relative_path(path) for path in accepted)
            self.accepted_hashes.update({relative_path(row["path"]): row["sha256"] for row in manifest})
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


def _json_snapshot(snapshot):
    return {
        "duration": snapshot["duration"],
        "effects": snapshot["effects"],
        "speaker": [dict(item) for item in snapshot["speaker"]],
    }


def _semantic_snapshot(value):
    if not isinstance(value, dict) or set(value) != {"duration", "effects", "speaker"}:
        raise ValueError("invalid_checkpoint_state")
    if value["effects"] != {} or not isinstance(value["speaker"], list):
        raise ValueError("invalid_checkpoint_state")
    try:
        speaker = tuple(sorted(tuple(sorted(item.items())) for item in value["speaker"] if isinstance(item, dict)))
        duration = float(value["duration"])
    except (AttributeError, TypeError, ValueError):
        raise ValueError("invalid_checkpoint_state") from None
    if len(speaker) != len(value["speaker"]) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("invalid_checkpoint_state")
    return {"duration": duration, "effects": {}, "speaker": speaker}


def _valid_effects(value):
    if not isinstance(value, dict):
        raise ValueError("invalid_checkpoint_state")
    for identifier, effect in value.items():
        if not isinstance(identifier, str) or not isinstance(effect, dict) or effect.get("id") != identifier:
            raise ValueError("invalid_checkpoint_state")
        if set(effect) != {"id", "src", "start", "duration", "track"}:
            raise ValueError("invalid_checkpoint_state")
        if not isinstance(effect["src"], str) or not effect["src"]:
            raise ValueError("invalid_checkpoint_state")
        if (not isinstance(effect["track"], int) or isinstance(effect["track"], bool)
                or not all(isinstance(effect[key], (int, float)) and not isinstance(effect[key], bool)
                           and math.isfinite(effect[key]) for key in ("start", "duration"))
                or effect["start"] < 0 or effect["duration"] <= 0):
            raise ValueError("invalid_checkpoint_state")
    return value


def _validate_checkpoint_state(state, root):
    required = {
        "schema", "status", "workspace", "project_id", "planned_duration", "baseline",
        "effects", "digest", "remote", "accepted_hashes", "publications",
    }
    if not isinstance(state, dict) or set(state) != required or state.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError("invalid_checkpoint_state")
    if state["status"] not in CHECKPOINT_STATUSES or state["workspace"] != str(root):
        raise ValueError("invalid_checkpoint_state")
    if not isinstance(state["project_id"], str) or not state["project_id"]:
        raise ValueError("invalid_checkpoint_state")
    baseline = _semantic_snapshot(state["baseline"])
    effects = _valid_effects(state["effects"])
    try:
        duration = float(state["planned_duration"])
    except (TypeError, ValueError):
        raise ValueError("invalid_checkpoint_state") from None
    if not math.isfinite(duration) or duration <= 0 or not math.isclose(
            baseline["duration"], duration, abs_tol=1e-6):
        raise ValueError("invalid_checkpoint_state")
    publications = state["publications"]
    if (not isinstance(publications, int) or isinstance(publications, bool)
            or publications < 0 or publications != len(effects)):
        raise ValueError("invalid_checkpoint_state")
    digest = state["digest"]
    if ((digest is not None and (not isinstance(digest, str) or not digest))
            or (publications > 0 and not digest)
            or (state["status"] == "ready" and publications == 0 and digest is not None)
            or (state["status"] == "finished" and publications == 0)):
        raise ValueError("invalid_checkpoint_state")
    remote = state["remote"]
    if (not isinstance(remote, list) or not all(isinstance(path, str) for path in remote)
            or len(remote) != len(set(remote))):
        raise ValueError("invalid_checkpoint_state")
    try:
        remote = [relative_path(path) for path in remote]
    except ValueError:
        raise ValueError("invalid_checkpoint_state") from None
    accepted_hashes = state["accepted_hashes"]
    if not isinstance(accepted_hashes, dict):
        raise ValueError("invalid_checkpoint_state")
    try:
        accepted_hashes = {relative_path(path): digest for path, digest in accepted_hashes.items()}
    except (AttributeError, ValueError):
        raise ValueError("invalid_checkpoint_state") from None
    if (not all(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
                for digest in accepted_hashes.values())
            or not set(accepted_hashes).issubset(remote)):
        raise ValueError("invalid_checkpoint_state")
    return {
        **state, "planned_duration": duration, "baseline": baseline,
        "effects": effects, "remote": remote, "accepted_hashes": accepted_hashes,
    }

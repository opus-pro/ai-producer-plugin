"""Validate one effect and checkpoint receipts from the current host MCP."""

from __future__ import annotations

import hashlib
import math
import mimetypes
import os
from pathlib import Path
import re
import shutil
import tempfile

from preflight import check
from publication_guard import inspect_index, validate_checkpoint_progress


MAX_FILES = 200
SIGN_BATCH_SIZE = 50
# The service includes its own runtime files in a host-authored commit receipt.
SERVER_RUNTIME_PATHS = frozenset({
    "render-engine/package.json",
    "render-engine/public/vendor/gsap.min.js",
    "render-engine/public/vendor/fit-engine.js",
    "render-engine/public/vendor/connector-engine.js",
})
CHECKPOINT_SCHEMA = 3
CHECKPOINT_STATUSES = frozenset({"ready", "prepared", "failed", "finished"})
_HASH = re.compile(r"[0-9a-f]{64}")
_WARNING = re.compile(r"[a-zA-Z0-9_-]{1,100}")


def relative_path(value):
    if not isinstance(value, str):
        raise ValueError("invalid_publication_path")
    if value.startswith("render-engine/"):
        value = value[len("render-engine/"):]
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError("invalid_publication_path")
    return path.as_posix()


def service_path(value):
    return "render-engine/" + relative_path(value)


class ProgressCheckpoint:
    """Keep one progressive publication safe without opening another Codex host."""

    def __init__(self, workspace, project_id, planned_duration, digest, remote=()):
        self.root = Path(workspace).resolve(strict=True)
        if not isinstance(project_id, str) or not project_id:
            raise ValueError("invalid_project_id")
        if not isinstance(digest, str) or not digest:
            raise ValueError("invalid_workspace_digest")
        self.project_id = project_id
        self.duration = float(planned_duration)
        if not math.isfinite(self.duration) or self.duration <= 0:
            raise ValueError("invalid_planned_duration")
        baseline = inspect_index((self.root / "index.html").read_text(encoding="utf-8"))
        if baseline["effects"] or not math.isclose(baseline["duration"], self.duration, abs_tol=1e-6):
            raise ValueError("full_timeline_base_required")
        self.baseline_snapshot = baseline
        self.effects = {}
        self.digest = digest
        self.remote = {relative_path(path) for path in remote}
        self.accepted_hashes = {}
        self.publications = 0
        self.status = "ready"
        self.pending = None
        self.warning_codes = []

    @classmethod
    def resume(cls, workspace, state):
        root = Path(workspace).resolve(strict=True)
        values = _validate_checkpoint_state(state, root)
        self = cls.__new__(cls)
        self.root = root
        self.project_id = values["project_id"]
        self.duration = values["planned_duration"]
        self.baseline_snapshot = values["baseline"]
        self.effects = values["effects"]
        self.digest = values["digest"]
        self.remote = set(values["remote"])
        self.accepted_hashes = values["accepted_hashes"]
        self.publications = values["publications"]
        self.status = values["status"]
        self.pending = values["pending"]
        self.warning_codes = values["warning_codes"]
        return self

    def checkpoint(self):
        return {
            "schema": CHECKPOINT_SCHEMA,
            "status": self.status,
            "workspace": str(self.root),
            "project_id": self.project_id,
            "planned_duration": self.duration,
            "baseline": _json_snapshot(self.baseline_snapshot),
            "effects": self.effects,
            "digest": self.digest,
            "remote": sorted(self.remote),
            "accepted_hashes": self.accepted_hashes,
            "publications": self.publications,
            "pending": self.pending,
            "warning_codes": self.warning_codes,
        }

    def _copy(self, relative, target):
        source = (self.root / relative).resolve(strict=True)
        if not source.is_relative_to(self.root) or not source.is_file():
            raise ValueError("publication_path_outside_workspace")
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        return destination

    def _snapshot(self, paths, target):
        for relative in self.remote.difference(paths):
            if Path(relative).suffix.lower() in {".html", ".css"} and (self.root / relative).is_file():
                self._copy(relative, target)
        manifest = []
        for relative in paths:
            file = self._copy(relative, target)
            manifest.append({
                "path": service_path(relative),
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                "content_type": mimetypes.guess_type(relative)[0] or "application/octet-stream",
            })
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

    def _prepare_draft(self, files, draft, final, save):
        """Validate an isolated next-effect draft before touching publication files."""
        source = Path(draft).resolve(strict=True)
        if not source.is_dir() or source.is_relative_to(self.root) or self.root.is_relative_to(source):
            raise ValueError("draft_must_be_outside_workspace")
        paths = [relative_path(path) for path in files]
        if not paths or len(paths) > MAX_FILES or len(set(paths)) != len(paths) or "index.html" not in paths:
            raise ValueError("invalid_publication_files")
        self._verify_accepted_files()
        with tempfile.TemporaryDirectory(prefix="aip-draft-") as directory:
            candidate_root = Path(directory).resolve()
            for relative in self.remote:
                if Path(relative).suffix.lower() in {".html", ".css"} and (self.root / relative).is_file():
                    self._copy(relative, candidate_root)
            for relative in paths:
                file = (source / relative).resolve(strict=True)
                destination = (self.root / relative).resolve()
                if not file.is_relative_to(source) or not file.is_file():
                    raise ValueError("draft_path_outside_workspace")
                if not destination.is_relative_to(self.root):
                    raise ValueError("publication_path_outside_workspace")
                target = candidate_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file, target)
            # Unlisted draft compositions must not silently bypass the one-effect contract.
            for file in (source / "compositions").rglob("*.html"):
                if file.relative_to(source).as_posix() not in paths:
                    raise ValueError("future_effect_files_present")
            candidate = type(self).resume(candidate_root, {
                **self.checkpoint(), "workspace": str(candidate_root),
            })
            plan = candidate.prepare(paths, final=final)
            def installed():
                self.pending = candidate.pending
                self.status = candidate.status
                if save is not None:
                    save(self.checkpoint())

            try:
                self._install_draft(candidate_root, paths, installed)
            except Exception:
                self.pending = None
                self.status = "ready"
                raise
        return plan

    def _install_draft(self, candidate, paths, installed_callback):
        """Replace validated files atomically per path, rolling back a failed batch."""
        with tempfile.TemporaryDirectory(prefix=".aip-install-", dir=self.root) as directory:
            stage = Path(directory)
            previous = set()
            for relative in paths:
                target = self.root / relative
                staged = stage / "new" / relative
                staged.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(candidate / relative, staged)
                if target.exists():
                    backup = stage / "old" / relative
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(target, backup)
                    previous.add(relative)
            installed = []
            try:
                for relative in paths:
                    target = self.root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(stage / "new" / relative, target)
                    installed.append(relative)
                installed_callback()
            except Exception:
                for relative in reversed(installed):
                    target = self.root / relative
                    if relative in previous:
                        os.replace(stage / "old" / relative, target)
                    else:
                        target.unlink()
                raise

    def prepare(self, files, *, final=False, draft=None, save=None):
        """Freeze the exact batch the current host must sign, upload, and commit."""
        if self.status != "ready":
            raise RuntimeError("publication_checkpoint_closed")
        if draft is not None:
            return self._prepare_draft(files, draft, final, save)
        paths = [relative_path(path) for path in files]
        if not paths or len(paths) > MAX_FILES or len(set(paths)) != len(paths) or "index.html" not in paths:
            raise ValueError("invalid_publication_files")
        candidate = (self.root / "index.html").read_text(encoding="utf-8")
        state = validate_checkpoint_progress(
            self.baseline_snapshot, self.effects, candidate, self.duration,
        )
        self._reject_unpublished_compositions(paths)
        self._verify_accepted_files()
        with tempfile.TemporaryDirectory(prefix="aip-publication-") as directory:
            snapshot = Path(directory).resolve()
            manifest = self._snapshot(paths, snapshot)
            if (snapshot / "index.html").read_text(encoding="utf-8") != candidate:
                raise RuntimeError("workspace_changed_during_snapshot")
        self.pending = {
            "duration": state["duration"],
            "effects": state["effects"],
            "files": manifest,
            "final": bool(final),
        }
        self.status = "prepared"
        return {
            "status": "prepared",
            "project_id": self.project_id,
            "base_digest": self.digest,
            "sign_batches": [
                [{"path": row["path"], "content_type": row["content_type"]} for row in batch]
                for offset in range(0, len(manifest), SIGN_BATCH_SIZE)
                for batch in (manifest[offset:offset + SIGN_BATCH_SIZE],)
            ],
            "expected_files": [{"path": row["path"], "sha256": row["sha256"]} for row in manifest],
            "authoring": not final,
            "published_effects": len(state["effects"]),
            "duration_seconds": state["duration"],
            "final": bool(final),
        }

    def accept(self, task_id, digest, accepted, warning_codes=()):
        """Advance only after the current host receives an accepted service receipt."""
        if self.status != "prepared" or self.pending is None:
            raise RuntimeError("publication_checkpoint_not_prepared")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("publication_task_missing")
        if not isinstance(digest, str) or not digest:
            raise ValueError("publication_receipt_digest_missing")
        if not isinstance(accepted, (list, tuple)) or not all(isinstance(path, str) for path in accepted):
            raise ValueError("publication_receipt_mismatch")
        accepted_paths = {service_path(path) for path in accepted}
        expected_paths = {row["path"] for row in self.pending["files"]}
        if not expected_paths.issubset(accepted_paths) or accepted_paths.difference(
                expected_paths, SERVER_RUNTIME_PATHS):
            raise ValueError("publication_receipt_mismatch")
        for row in self.pending["files"]:
            relative = relative_path(row["path"])
            file = self.root / relative
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError("prepared_file_changed")
        warnings = sorted({code for code in warning_codes if isinstance(code, str) and _WARNING.fullmatch(code)})
        self.warning_codes = sorted(set(self.warning_codes).union(warnings))
        final = self.pending["final"]
        self.effects = self.pending["effects"]
        self.digest = digest
        self.remote.update(relative_path(path) for path in accepted_paths)
        self.accepted_hashes.update({relative_path(row["path"]): row["sha256"] for row in self.pending["files"]})
        self.publications += 1
        self.pending = None
        self.status = "finished" if final else "ready"
        return {
            "published_effects": len(self.effects),
            "duration_seconds": self.duration,
            "task_id": task_id,
            "final": final,
            "warning_codes": self.warning_codes,
        }


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


def _valid_manifest(value):
    if not isinstance(value, list) or not value or len(value) > MAX_FILES:
        raise ValueError("invalid_checkpoint_state")
    paths = set()
    manifest = []
    for row in value:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "content_type"}:
            raise ValueError("invalid_checkpoint_state")
        path = service_path(row["path"])
        if path in paths or not isinstance(row["sha256"], str) or not _HASH.fullmatch(row["sha256"]):
            raise ValueError("invalid_checkpoint_state")
        if not isinstance(row["content_type"], str) or not row["content_type"]:
            raise ValueError("invalid_checkpoint_state")
        paths.add(path)
        manifest.append({**row, "path": path})
    if "render-engine/index.html" not in paths:
        raise ValueError("invalid_checkpoint_state")
    return manifest


def _valid_pending(value, effects, duration, status):
    if status != "prepared":
        if value is not None:
            raise ValueError("invalid_checkpoint_state")
        return None
    if not isinstance(value, dict) or set(value) != {"duration", "effects", "files", "final"}:
        raise ValueError("invalid_checkpoint_state")
    pending_effects = _valid_effects(value["effects"])
    if len(pending_effects) != len(effects) + 1 or any(pending_effects.get(key) != item for key, item in effects.items()):
        raise ValueError("invalid_checkpoint_state")
    try:
        pending_duration = float(value["duration"])
    except (TypeError, ValueError):
        raise ValueError("invalid_checkpoint_state") from None
    if not math.isclose(pending_duration, duration, abs_tol=1e-6) or not isinstance(value["final"], bool):
        raise ValueError("invalid_checkpoint_state")
    return {**value, "duration": pending_duration, "effects": pending_effects,
            "files": _valid_manifest(value["files"])}


def _validate_checkpoint_state(state, root):
    required = {
        "schema", "status", "workspace", "project_id", "planned_duration", "baseline",
        "effects", "digest", "remote", "accepted_hashes", "publications", "pending", "warning_codes",
    }
    if isinstance(state, dict) and state.get("schema") == 2:
        if set(state) != required - {"warning_codes"} or state.get("status") not in {
                "ready", "prepared", "finished"}:
            raise ValueError("invalid_checkpoint_state")
        # Older checkpoints did not retain warning codes; upgrade on the next save.
        state = {**state, "schema": CHECKPOINT_SCHEMA, "warning_codes": []}
    if not isinstance(state, dict) or set(state) != required or state.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError("invalid_checkpoint_state")
    status = state["status"]
    if status not in CHECKPOINT_STATUSES or state["workspace"] != str(root):
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
            or publications < 0 or publications != len(effects)
            or (status == "finished" and publications == 0)):
        raise ValueError("invalid_checkpoint_state")
    digest = state["digest"]
    if not isinstance(digest, str) or not digest:
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
        accepted_hashes = {relative_path(path): value for path, value in accepted_hashes.items()}
    except (AttributeError, ValueError):
        raise ValueError("invalid_checkpoint_state") from None
    if (not all(isinstance(value, str) and _HASH.fullmatch(value) for value in accepted_hashes.values())
            or not set(accepted_hashes).issubset(remote)):
        raise ValueError("invalid_checkpoint_state")
    pending = _valid_pending(state["pending"], effects, duration, status)
    warning_codes = state["warning_codes"]
    if (not isinstance(warning_codes, list) or not all(
            isinstance(code, str) and _WARNING.fullmatch(code) for code in warning_codes)):
        raise ValueError("invalid_checkpoint_state")
    return {
        **state,
        "planned_duration": duration,
        "baseline": baseline,
        "effects": effects,
        "remote": remote,
        "accepted_hashes": accepted_hashes,
        "pending": pending,
    }

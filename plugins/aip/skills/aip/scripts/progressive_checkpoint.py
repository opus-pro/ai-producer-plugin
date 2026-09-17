#!/usr/bin/env python3
"""Persist progressive AIP state while the current host performs MCP calls."""

from __future__ import annotations

import argparse
from contextlib import contextmanager, ExitStack
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import tempfile
import time

from progressive_publish import ProgressCheckpoint


MAX_CHECKPOINT_BYTES = 1024 * 1024
SAFE_ERROR = re.compile(r"[\x20-\x7e]{1,1200}")
MAX_JOIN_SECONDS = 600
JOIN_INTERVAL_SECONDS = 0.1
SETTLEMENT_LOCK_SECONDS = 10


def _canonical(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _state_path(value, workspace):
    root = Path(workspace).resolve(strict=True)
    supplied = Path(value).expanduser()
    parent = supplied.parent.resolve(strict=True)
    path = parent / supplied.name
    if path.is_relative_to(root) or path.is_symlink():
        raise ValueError("checkpoint_must_be_outside_workspace")
    return path


def _set_private_mode(descriptor):
    fchmod = getattr(os, "fchmod", None)
    if callable(fchmod):
        fchmod(descriptor, 0o600)


def _sync_directory(path):
    if os.name == "nt":
        return
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY)
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        if descriptor is not None:
            os.close(descriptor)


@contextmanager
def checkpoint_lock(path):
    """Hold one cross-process lock for the complete checkpoint transition."""
    lock_path = Path(path).with_name(Path(path).name + ".lock")
    if lock_path.is_symlink():
        raise ValueError("invalid_checkpoint_lock")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock_path, flags, 0o600)
        _set_private_mode(descriptor)
        if os.name == "nt":
            import msvcrt
            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, ImportError):
        try:
            os.close(descriptor)
        except (OSError, UnboundLocalError):
            pass
        raise RuntimeError("publication_checkpoint_busy") from None
    try:
        yield
    finally:
        if os.name == "nt":
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def write_checkpoint(path, state):
    """Atomically replace a checksum-protected, credential-free checkpoint."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError("invalid_checkpoint_path")
    encoded = _canonical(state)
    envelope = _canonical({"sha256": hashlib.sha256(encoded).hexdigest(), "state": state}) + b"\n"
    if len(envelope) > MAX_CHECKPOINT_BYTES:
        raise ValueError("checkpoint_too_large")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        _set_private_mode(descriptor)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(envelope)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _sync_directory(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            Path(temporary).unlink()
        except FileNotFoundError:
            pass


def read_checkpoint(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_CHECKPOINT_BYTES:
        raise ValueError("invalid_checkpoint_file")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("invalid_checkpoint_file") from None
    if not isinstance(envelope, dict) or set(envelope) != {"sha256", "state"}:
        raise ValueError("invalid_checkpoint_file")
    digest = envelope["sha256"]
    if not isinstance(digest, str) or not hmac.compare_digest(
            digest, hashlib.sha256(_canonical(envelope["state"])).hexdigest()):
        raise ValueError("invalid_checkpoint_checksum")
    return envelope["state"]


def initialize(workspace, state_path, project_id, duration, digest, remote_files=()):
    root = Path(workspace).resolve(strict=True)
    checkpoint = _state_path(state_path, root)
    with checkpoint_lock(checkpoint):
        if checkpoint.exists():
            raise ValueError("checkpoint_already_exists")
        progress = ProgressCheckpoint(root, project_id, duration, digest, remote_files)
        write_checkpoint(checkpoint, progress.checkpoint())
    return {"status": "ready", "published_effects": 0, "duration_seconds": progress.duration}


@contextmanager
def accepted_checkpoint(checkpoint, count, wait_seconds, batch_join=False):
    """Wait on atomic local receipts without MCP calls or model continuations."""
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("invalid_previous_effect_count")
    if not 0 <= wait_seconds <= MAX_JOIN_SECONDS:
        raise ValueError("invalid_publication_wait")
    deadline = time.monotonic() + wait_seconds
    while True:
        with ExitStack() as held:
            try:
                held.enter_context(checkpoint_lock(checkpoint))
            except RuntimeError as error:
                if str(error) != "publication_checkpoint_busy":
                    raise
            else:
                state = read_checkpoint(checkpoint)
                if state["status"] == "ready" and state["publications"] == count:
                    yield
                    return
                waiting = state["status"] == "prepared" and state["publications"] == count - 1
                if batch_join:
                    waiting = (state["status"] in {"ready", "prepared"}
                               and max(0, count - 2) <= state["publications"] < count)
                if not waiting:
                    raise RuntimeError("previous_publication_not_accepted")
        if time.monotonic() >= deadline:
            raise TimeoutError("publication_join_timeout")
        time.sleep(JOIN_INTERVAL_SECONDS)


def prepare(workspace, state_path, files, final=False, draft=None, after_effect=None,
            wait_seconds=MAX_JOIN_SECONDS, batch_join=False):
    root = Path(workspace).resolve(strict=True)
    checkpoint = _state_path(state_path, root)
    if batch_join and (after_effect is None or draft is None):
        raise ValueError("batch_join_requires_previous_effect_and_draft")
    lock = (checkpoint_lock(checkpoint) if after_effect is None
            else accepted_checkpoint(checkpoint, after_effect, wait_seconds, batch_join))
    with lock:
        progress = ProgressCheckpoint.resume(root, read_checkpoint(checkpoint))
        if after_effect is not None and progress.publications != after_effect:
            raise RuntimeError("previous_publication_not_accepted")
        report = progress.prepare(files, final=final, draft=draft,
                                  save=lambda state: write_checkpoint(checkpoint, state))
        if draft is None:
            write_checkpoint(checkpoint, progress.checkpoint())
        return report


@contextmanager
def settlement_lock(checkpoint):
    """Let receipt writes outlast a concurrent join poll without replaying work."""
    deadline = time.monotonic() + SETTLEMENT_LOCK_SECONDS
    while True:
        with ExitStack() as held:
            try:
                held.enter_context(checkpoint_lock(checkpoint))
            except RuntimeError as error:
                if str(error) != "publication_checkpoint_busy":
                    raise
            else:
                yield
                return
        if time.monotonic() >= deadline:
            raise TimeoutError("publication_settlement_lock_timeout")
        time.sleep(JOIN_INTERVAL_SECONDS)


def fail(workspace, state_path, effect):
    """Close a failed step, including draft validation, so later batches stop."""
    root = Path(workspace).resolve(strict=True)
    checkpoint = _state_path(state_path, root)
    if not isinstance(effect, int) or isinstance(effect, bool) or effect < 1:
        raise ValueError("invalid_failed_effect_count")
    with settlement_lock(checkpoint):
        progress = ProgressCheckpoint.resume(root, read_checkpoint(checkpoint))
        if progress.publications >= effect:
            return {"status": "already_accepted", "published_effects": progress.publications}
        prepared = (progress.status == "prepared" and progress.pending is not None
                    and len(progress.pending["effects"]) == effect)
        next_draft = progress.status == "ready" and progress.publications == effect - 1
        if not (prepared or next_draft):
            raise RuntimeError("publication_failure_mismatch")
        progress.status = "failed"
        progress.pending = None
        write_checkpoint(checkpoint, progress.checkpoint())
    return {"status": "failed", "published_effects": progress.publications}


def accept(workspace, state_path, task_id, digest, accepted_files, warning_codes=()):
    root = Path(workspace).resolve(strict=True)
    checkpoint = _state_path(state_path, root)
    with settlement_lock(checkpoint):
        progress = ProgressCheckpoint.resume(root, read_checkpoint(checkpoint))
        report = progress.accept(task_id, digest, accepted_files, warning_codes)
        write_checkpoint(checkpoint, progress.checkpoint())
        return report


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--workspace", required=True)
    init.add_argument("--state", required=True)
    init.add_argument("--project-id", required=True)
    init.add_argument("--duration", required=True, type=float)
    init.add_argument("--base-digest", required=True)
    init.add_argument("--remote-file", action="append", default=[])
    step = commands.add_parser("prepare")
    step.add_argument("--workspace", required=True)
    step.add_argument("--state", required=True)
    step.add_argument("--file", action="append", required=True)
    step.add_argument("--final", action="store_true")
    step.add_argument("--draft", help="Isolated next-effect files, outside the publication workspace")
    step.add_argument("--after-effect", type=int, help="Join this accepted effect before preparing a draft")
    step.add_argument("--batch-join", action="store_true",
                      help="Allow the preceding two-effect batch to reach its final receipt")
    step.add_argument("--wait-seconds", type=float, default=MAX_JOIN_SECONDS)
    failed = commands.add_parser("fail")
    failed.add_argument("--workspace", required=True)
    failed.add_argument("--state", required=True)
    failed.add_argument("--effect", required=True, type=int)
    receipt = commands.add_parser("accept")
    receipt.add_argument("--workspace", required=True)
    receipt.add_argument("--state", required=True)
    receipt.add_argument("--task-id", required=True)
    receipt.add_argument("--digest", required=True)
    receipt.add_argument("--accepted-file", action="append", required=True)
    receipt.add_argument("--warning-code", action="append", default=[])
    return parser


def main():
    args = _parser().parse_args()
    try:
        if args.command == "init":
            report = initialize(
                args.workspace, args.state, args.project_id, args.duration,
                args.base_digest, args.remote_file,
            )
        elif args.command == "prepare":
            report = prepare(args.workspace, args.state, args.file, args.final, args.draft,
                             args.after_effect, args.wait_seconds, args.batch_join)
        elif args.command == "fail":
            report = fail(args.workspace, args.state, args.effect)
        else:
            report = accept(
                args.workspace, args.state, args.task_id, args.digest,
                args.accepted_file, args.warning_code,
            )
        print(json.dumps(report, separators=(",", ":")), flush=True)
    except Exception as error:
        message = str(error)
        if not SAFE_ERROR.fullmatch(message) or "://" in message:
            message = "checkpoint_command_failed"
        raise SystemExit(message) from None


if __name__ == "__main__":
    main()

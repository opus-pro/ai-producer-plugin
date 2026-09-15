#!/usr/bin/env python3
"""Persist one accepted AIP publication between host-model checkpoints."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import tempfile

from codex_mcp import CodexMcp
from progressive_publish import ProgressPublisher

MAX_CHECKPOINT_BYTES = 1024 * 1024
SAFE_ERROR = re.compile(r"[\x20-\x7e]{1,1200}")


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


def initialize(workspace, state_path, project_id, duration):
    root = Path(workspace).resolve(strict=True)
    checkpoint = _state_path(state_path, root)
    with checkpoint_lock(checkpoint):
        if checkpoint.exists():
            raise ValueError("checkpoint_already_exists")
        publisher = ProgressPublisher(root, project_id, duration, transport=None)
        write_checkpoint(checkpoint, publisher.checkpoint())
    print(json.dumps({"status": "ready", "published_effects": 0,
                      "duration_seconds": publisher.duration}, separators=(",", ":")), flush=True)


def publish(workspace, state_path, server, files, final=False, cli=None,
            mcp_factory=CodexMcp, uploader=None, on_progress=None):
    root = Path(workspace).resolve(strict=True)
    checkpoint = _state_path(state_path, root)
    with checkpoint_lock(checkpoint):
        state = read_checkpoint(checkpoint)
        options = {}
        if uploader is not None:
            options["uploader"] = uploader
        if on_progress is not None:
            options["on_progress"] = on_progress
        with mcp_factory(server, root, cli=cli) as mcp:
            publisher = ProgressPublisher.resume(root, state, mcp, **options)
            write_checkpoint(checkpoint, publisher.checkpoint("publishing"))
            try:
                report = publisher.publish(files, final=final)
            except Exception:
                write_checkpoint(checkpoint, publisher.checkpoint("failed"))
                raise
            write_checkpoint(checkpoint, publisher.checkpoint())
            return report


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--workspace", required=True)
    init.add_argument("--state", required=True)
    init.add_argument("--project-id", required=True)
    init.add_argument("--duration", required=True, type=float)
    step = commands.add_parser("publish")
    step.add_argument("--workspace", required=True)
    step.add_argument("--state", required=True)
    step.add_argument("--server", required=True)
    step.add_argument("--codex-cli")
    step.add_argument("--file", action="append", required=True)
    step.add_argument("--final", action="store_true")
    return parser


def main():
    args = _parser().parse_args()
    try:
        if args.command == "init":
            initialize(args.workspace, args.state, args.project_id, args.duration)
        else:
            publish(args.workspace, args.state, args.server, args.file, args.final, args.codex_cli)
    except Exception as error:
        message = str(error)
        if not SAFE_ERROR.fullmatch(message) or "://" in message:
            message = "checkpoint_command_failed"
        raise SystemExit(message) from None


if __name__ == "__main__":
    main()

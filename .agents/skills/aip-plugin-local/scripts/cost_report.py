#!/usr/bin/env python3
"""Read Codex usage receipts without exporting conversation content."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from collections import Counter
from datetime import date
from pathlib import Path

TOKEN_KEYS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens", "total_tokens",
)
TASK_ID = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")


def task_id(value: str) -> str:
    value = value.removeprefix("codex://threads/").rstrip("/")
    if not TASK_ID.fullmatch(value):
        raise ValueError("Expected a Codex task ID or codex://threads/<id> link")
    return value


def session_index(root: Path) -> dict:
    index = {}
    for path in sorted(root.rglob("*.jsonl")):
        with path.open(encoding="utf-8") as stream:
            first = stream.readline()
        try:
            row = json.loads(first)
        except json.JSONDecodeError:
            continue
        if row.get("type") != "session_meta":
            continue
        meta = row["payload"]
        identifier = meta.get("id")
        source = meta.get("source", {})
        parent = None
        if isinstance(source, dict):
            subagent = source.get("subagent")
            spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
            parent = spawn.get("parent_thread_id") if isinstance(spawn, dict) else None
        if identifier in index:
            raise ValueError("Duplicate task files in sessions root; select an unambiguous source")
        if identifier:
            index[identifier] = {"path": path, "parent": parent}
    return index


def validate_rates(rates: dict) -> None:
    if not rates.get("source"):
        raise ValueError("Rates require their official source URL")
    date.fromisoformat(rates["verified_on"])
    for quote in rates["models"].values():
        if not quote.get("tier") or "long_context" not in quote:
            raise ValueError("Each rate needs a tier and an explicit long_context policy")
        values = [quote[key] for key in ("input", "cached", "output")]
        long = quote["long_context"]
        if long is not None:
            if long["threshold"] <= 0:
                raise ValueError("Long-context threshold must be positive")
            values += [long[key] for key in ("input_multiplier", "cached_multiplier", "output_multiplier")]
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0 for v in values):
            raise ValueError("Rates and multipliers must be finite nonnegative numbers")


def price(usage: dict, context: dict, rates: dict | None) -> tuple[float | None, str]:
    model = context.get("model")
    quote = (rates or {}).get("models", {}).get(model)
    if quote is None:
        return None, "No verified rate for the recorded model"
    tier = context.get("service_tier")
    compatible = tier == quote["tier"] or (tier in (None, "default") and quote["tier"] == "standard")
    if not compatible:
        return None, "Recorded tier does not match the supplied rate"
    if usage["cache_write_input_tokens"]:
        return None, "Cache-write accounting requires a verified pricing implementation"
    multipliers = (1, 1, 1)
    long = quote["long_context"]
    if long and usage["input_tokens"] > long["threshold"]:
        multipliers = tuple(long[k] for k in ("input_multiplier", "cached_multiplier", "output_multiplier"))
    uncached = usage["input_tokens"] - usage["cached_input_tokens"]
    cost = (
        uncached * quote["input"] * multipliers[0]
        + usage["cached_input_tokens"] * quote["cached"] * multipliers[1]
        + usage["output_tokens"] * quote["output"] * multipliers[2]
    ) / 1_000_000
    basis = "Standard API equivalent; recorded tier unavailable" if tier is None else "API equivalent at supplied tier"
    return cost, basis


def read_usage(identifier: str, entry: dict, rates: dict | None, selected_turn: str | None = None,
               inherited_turns: set | None = None) -> dict:
    contexts, receipts, completed = {}, {}, {}
    started, foreign_turns = set(), set()
    cumulative = None
    partial_tail = False
    with entry["path"].open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                if not line.endswith("\n"):
                    partial_tail = True
                    break
                raise ValueError(f"Invalid JSON in task {identifier}, line {line_number}") from None
            data = row.get("payload", {})
            if row.get("type") == "turn_context":
                contexts[data.get("turn_id")] = {k: data.get(k) for k in ("model", "effort", "service_tier")}
            elif row.get("type") == "event_msg" and data.get("type") == "task_started":
                started.add(data.get("turn_id"))
            elif row.get("type") == "event_msg" and data.get("type") == "task_complete":
                completed[data.get("turn_id")] = data.get("duration_ms")
            elif row.get("type") == "token_usage_record" and data.get("thread_id") != identifier:
                foreign_turns.add(data.get("turn_id"))
            elif row.get("type") == "token_usage_record" and data.get("thread_id") == identifier:
                response_id = data["response_id"]
                usage = data["usage"]
                if any(not isinstance(usage.get(k), int) or isinstance(usage[k], bool) or usage[k] < 0 for k in TOKEN_KEYS):
                    raise ValueError(f"Incomplete or invalid usage receipt in task {identifier}")
                if usage["cached_input_tokens"] > usage["input_tokens"] or usage["reasoning_output_tokens"] > usage["output_tokens"]:
                    raise ValueError("Token subset exceeds its parent count")
                if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
                    raise ValueError("Receipt total does not equal input plus output")
                if response_id in receipts:
                    if receipts[response_id]["usage"] != usage:
                        raise ValueError("Conflicting duplicate response receipt")
                    continue
                context = contexts.get(data.get("turn_id"), {})
                usd, basis = price(usage, context, rates)
                receipts[response_id] = {
                    "sequence": len(receipts) + 1, "response_id": response_id,
                    "turn_id": data.get("turn_id"), "root_turn_id": data.get("root_turn_id"),
                    "timestamp": row.get("timestamp"), **context,
                    "usage": {k: usage[k] for k in TOKEN_KEYS}, "usd": usd, "pricing_basis": basis,
                }
                cumulative = data.get("thread_token_usage")
    full_totals = Counter({key: 0 for key in TOKEN_KEYS})
    for record in receipts.values():
        full_totals.update(record["usage"])
    reconciled = cumulative is not None and all(full_totals[key] == cumulative.get(key) for key in TOKEN_KEYS)
    receipt_turns = {record["turn_id"] for record in receipts.values()}
    turns = (started | contexts.keys() | receipt_turns) - foreign_turns - (inherited_turns or set()) - {None}
    unassigned = turns - receipt_turns
    selected = [r for r in receipts.values() if selected_turn is None or selected_turn in (r["turn_id"], r["root_turn_id"])]
    relevant_turns = turns if selected_turn is None else {r["turn_id"] for r in selected}
    if selected_turn in turns:
        relevant_turns.add(selected_turn)
    if entry["parent"] and selected_turn is not None:
        relevant_turns |= unassigned
    totals = Counter({key: 0 for key in TOKEN_KEYS})
    for record in selected:
        totals.update(record["usage"])
    issues = []
    if not receipts:
        issues.append("No response usage receipts available")
    elif not reconciled:
        issues.append("Per-response sum does not reconcile with the final thread cumulative usage")
    if relevant_turns & unassigned:
        issues.append("Started/context turns without usage receipts; their cost is not yet available")
    is_complete = bool(relevant_turns) and relevant_turns <= completed.keys() and not (relevant_turns & unassigned) and not partial_tail
    elapsed = sum(completed[t] for t in relevant_turns) if is_complete and all(isinstance(completed[t], int) for t in relevant_turns) else None
    priced = bool(selected) and reconciled and all(r["usd"] is not None for r in selected)
    return {
        "thread_id": identifier, "parent_id": entry["parent"], "complete": is_complete,
        "elapsed_ms": elapsed, "partial_tail": partial_tail, "responses": len(selected),
        "tokens": dict(totals), "usd": round(sum(r["usd"] for r in selected), 9) if priced else None,
        "reconciled": reconciled, "issues": issues, "rows": selected,
        "turn_ids": sorted(turns), "unassigned_turn_ids": sorted(unassigned),
    }


def report(identifier: str, sessions: Path, rates: dict | None = None, selected_turn: str | None = None) -> dict:
    if rates is not None:
        validate_rates(rates)
    index = session_index(sessions)
    if identifier not in index:
        raise ValueError("Task not found in the supplied local sessions root")
    threads, ancestors, queue = [], {identifier: set()}, [identifier]
    for key in queue:
        current = read_usage(key, index[key], rates, selected_turn, ancestors[key])
        if key == identifier and selected_turn is not None and selected_turn not in current["turn_ids"]:
            raise ValueError("Selected turn is not present in the root task")
        if selected_turn is None or key == identifier or current["responses"] or current["unassigned_turn_ids"] or not current["reconciled"]:
            threads.append(current)
        for child, entry in sorted(index.items()):
            if entry["parent"] == key and child not in ancestors:
                ancestors[child] = ancestors[key] | set(current["turn_ids"])
                queue.append(child)
    tokens = {key: sum(t["tokens"][key] for t in threads) for key in TOKEN_KEYS}
    fully_priced = all(t["usd"] is not None for t in threads)
    return {
        "root_thread_id": identifier,
        "scope": {"root_turn_id": selected_turn} if selected_turn else "All turns, including follow-ups",
        "basis": "Client model tokens only; excludes backend and separate tool charges. Not a subscription invoice.",
        "pricing_source": (rates or {}).get("source"), "pricing_verified_on": (rates or {}).get("verified_on"),
        "complete": all(t["complete"] for t in threads), "elapsed_ms": threads[0]["elapsed_ms"],
        "responses": sum(t["responses"] for t in threads), "tokens": tokens,
        "usd": round(sum(t["usd"] for t in threads), 9) if fully_priced else None,
        "threads": threads,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=task_id)
    parser.add_argument("--sessions-root", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions")
    parser.add_argument("--rates", type=Path)
    parser.add_argument("--turn", type=task_id, help="Count one root turn and its descendants, excluding later follow-ups")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        rates = json.loads(args.rates.read_text()) if args.rates else None
        result = report(args.task, args.sessions_root, rates, args.turn)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        summary = {k: v for k, v in result.items() if k != "threads"}
        summary["threads"] = [{k: v for k, v in t.items() if k != "rows"} for t in result["threads"]]
        print(json.dumps(summary, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Cannot produce a complete cost report: {error}\n")


if __name__ == "__main__":
    main()

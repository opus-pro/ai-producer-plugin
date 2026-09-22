#!/usr/bin/env python3
"""Score observable Motion Library handoff traces against synthetic scenarios."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


SCENARIOS = Path(__file__).with_name("scenarios.json")


def load_scenarios(path: Path = SCENARIOS) -> dict[str, dict[str, Any]]:
    records = json.loads(path.read_text(encoding="utf-8"))
    scenarios = {record["id"]: record for record in records}
    if len(scenarios) != len(records):
        raise ValueError("scenario ids must be unique")
    for record in records:
        if record["id"] == "legacy-reference-here":
            continue
        match = re.search(r"https://producer\.opus\.pro/r/(aipr_[A-Za-z0-9_-]{16})", record["request"])
        if not match:
            raise ValueError(f"{record['id']}: invalid synthetic reference URL")
        resolved = record["resolved"]
        if set(resolved) != {"schema_version", "project_id", "references"} or resolved["schema_version"] != 2:
            raise ValueError(f"{record['id']}: resolver envelope does not match v2")
        if len(resolved["references"]) != 1:
            raise ValueError(f"{record['id']}: fixture must resolve exactly one reference")
        reference = resolved["references"][0]
        required = {
            "project_id", "kind", "address", "composition_id", "at_ms", "region",
            "reference_id", "expires_at", "intent", "placement", "context", "availability",
        }
        if set(reference) != required:
            raise ValueError(f"{record['id']}: resolver fixture fields do not match v2")
        if reference["reference_id"] != match.group(1):
            raise ValueError(f"{record['id']}: reference id does not match URL")
        if reference["placement"]["mode"] == "auto" and reference["at_ms"] is not None:
            raise ValueError(f"{record['id']}: auto placement must have null compatibility at_ms")
        if reference["placement"]["mode"] == "explicit" and reference["at_ms"] != reference["placement"]["at_ms"]:
            raise ValueError(f"{record['id']}: explicit compatibility at_ms must match placement")
    return scenarios


def model_cases(scenarios: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Return model inputs without baseline or candidate answer fields."""
    return [
        {
            "scenario_id": scenario["id"],
            "request": scenario["request"],
            "resolved": scenario["resolved"],
            "context": scenario["context"],
        }
        for scenario in scenarios.values()
    ]


def trace_set_failures(scenarios: dict[str, Any], traces: list[dict[str, Any]]) -> list[str]:
    """Require exactly one candidate trace for every scenario."""
    ids = [trace.get("scenario_id") for trace in traces]
    ordered_ids = sorted(set(ids), key=lambda value: str(value))
    failures = [f"duplicate:{scenario_id}" for scenario_id in ordered_ids if ids.count(scenario_id) > 1]
    failures.extend(f"missing:{scenario_id}" for scenario_id in sorted(set(scenarios) - set(ids)))
    failures.extend(f"unknown:{scenario_id}" for scenario_id in ordered_ids if scenario_id not in scenarios)
    return failures


def _ordered(actual: list[str], required: list[str]) -> bool:
    position = 0
    for name in actual:
        if position < len(required) and name == required[position]:
            position += 1
    return position == len(required)


def evaluate(scenario: dict[str, Any], trace: dict[str, Any]) -> list[str]:
    """Return stable rubric failures for one candidate execution trace."""
    expected = scenario["expected"]
    calls = trace.get("calls", [])
    call_names = [call.get("name") for call in calls]
    failures: list[str] = []

    if trace.get("route") != expected["route"]:
        failures.append("route")
    if not calls or call_names[0] != "resolve_selection":
        failures.append("resolve_first")
    elif calls[0].get("arguments", {}).get("selection") != scenario["request"]:
        failures.append("resolve_whole_request")
    if not _ordered(call_names, expected["required_call_order"]):
        failures.append("required_call_order")
    if set(call_names).intersection(expected["forbidden_calls"]):
        failures.append("forbidden_call")

    missing_reads = set(expected.get("context_reads", [])) - set(trace.get("context_reads", []))
    if missing_reads:
        failures.append("context_reads")

    window = expected.get("window")
    if window is not None:
        if trace.get("window") != window:
            failures.append("window")
        listings = [call for call in calls if call.get("name") == "list_motion_assets"]
        if not listings or any(
            listing.get("arguments", {}).get("at_ms") != window["at_ms"]
            or listing.get("arguments", {}).get("duration_ms") != window["duration_ms"]
            for listing in listings
        ):
            failures.append("list_final_window")

    materializations = [call for call in calls if call.get("name") == "materialize_motion_asset"]
    if expected["route"] == "materialize":
        if len(materializations) != 1:
            failures.append("materialize_count")
        else:
            arguments = materializations[0].get("arguments", {})
            if (
                arguments.get("timeline_in_ms") != window["at_ms"]
                or arguments.get("duration_ms") != window["duration_ms"]
            ):
                failures.append("materialize_window")
            if arguments.get("expected_project_revision") != scenario["context"]["listing_project_revision"]:
                failures.append("materialize_revision")
            if set(arguments.get("parameters", {})) != set(expected["parameter_keys"]):
                failures.append("materialize_parameter_keys")
            if "media_inputs" in expected and arguments.get("media_inputs") != expected["media_inputs"]:
                failures.append("materialize_media_inputs")

    expected_frame_calls = (
        scenario["context"].get("listing_entry", {})
        .get("next_data", {})
        .get("cutout", {})
        .get("frame_speaker_calls")
    )
    if expected_frame_calls is not None:
        actual_frame_calls = [call.get("arguments", {}) for call in calls if call.get("name") == "frame_speaker"]
        if actual_frame_calls != expected_frame_calls:
            failures.append("frame_speaker_calls")

    questions = trace.get("questions", [])
    if len(questions) < expected.get("min_questions", 0):
        failures.append("too_few_questions")
    if len(questions) > expected["max_questions"]:
        failures.append("too_many_questions")
    if bool(trace.get("refused")) != expected["refused"]:
        failures.append("refusal")
    if expected["requires_grounded_values"] and not trace.get("grounded_values"):
        failures.append("grounded_values")

    serialized = json.dumps(trace, sort_keys=True)
    if any(term in serialized for term in expected["forbidden_literals"]):
        failures.append("demo_leakage")
    if expected.get("cutout_windows") != trace.get("cutout_windows"):
        if "cutout_windows" in expected:
            failures.append("cutout_windows")
    if expected["requires_page_url"]:
        if not trace.get("page_url") or trace.get("agent_page_url"):
            failures.append("durable_page_url")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", nargs="?", type=Path, help="JSON array of candidate traces")
    parser.add_argument("--scenarios", type=Path, default=SCENARIOS)
    parser.add_argument("--emit-model-cases", action="store_true")
    args = parser.parse_args()
    scenarios = load_scenarios(args.scenarios)
    if args.emit_model_cases:
        print(json.dumps(model_cases(scenarios), indent=2))
        return 0
    if args.candidate is None:
        parser.error("candidate is required unless --emit-model-cases is used")
    traces = json.loads(args.candidate.read_text(encoding="utf-8"))
    set_failures = trace_set_failures(scenarios, traces)
    for failure in set_failures:
        print(f"trace_set: {failure}")
    failed = bool(set_failures)
    for trace in traces:
        scenario_id = trace.get("scenario_id")
        if scenario_id not in scenarios:
            continue
        failures = evaluate(scenarios[scenario_id], trace)
        print(f"{scenario_id}: {'PASS' if not failures else ','.join(failures)}")
        failed = failed or bool(failures)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())

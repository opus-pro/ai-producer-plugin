#!/usr/bin/env python3
"""Score observable Motion Library handoff traces against synthetic scenarios."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


SCENARIOS = Path(__file__).with_name("scenarios.json")
PRIMARY_CONTEXT = re.compile(
    r"(?:Project|项目)\s*[：:]\s*`?([A-Za-z0-9_-]+)`?\s*(?:\||·)\s*"
    r"(?:Template|模板)\s*[：:]\s*`?([A-Za-z0-9._-]+)@([0-9A-Za-z.+-]+)`?"
)
ROUTES = {"materialize", "derive", "needs_input", "refuse", "needs_context", "ordinary_project"}


def load_scenarios(path: Path = SCENARIOS) -> dict[str, dict[str, Any]]:
    records = json.loads(path.read_text(encoding="utf-8"))
    scenarios = {record["id"]: record for record in records}
    if len(scenarios) != len(records):
        raise ValueError("scenario ids must be unique")
    for record in records:
        source = record["source"]
        expected = record["expected"]
        if expected["route"] not in ROUTES:
            raise ValueError(f"{record['id']}: unknown route")
        matches = PRIMARY_CONTEXT.findall(record["request"])
        if source == "primary" and "handoff" in record:
            if len(matches) != 1:
                raise ValueError(f"{record['id']}: primary fixture must have one context line")
            project_id, motion_asset_id, version = matches[0]
            if record["handoff"] != {
                "project_id": project_id,
                "motion_asset_id": motion_asset_id,
                "version": version,
            }:
                raise ValueError(f"{record['id']}: parsed context does not match handoff")
            if "@aip" in record["request"] or "/r/" in record["request"]:
                raise ValueError(f"{record['id']}: primary handoff uses a legacy marker")
        if source == "legacy" and "@aip" not in record["request"]:
            raise ValueError(f"{record['id']}: legacy fixture lacks marker")
        if source == "ordinary" and matches:
            raise ValueError(f"{record['id']}: ordinary request parsed as a handoff")
    return scenarios


def model_cases(scenarios: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Return model inputs without contract intent, parsed answer or rubric fields."""
    cases = []
    for scenario in scenarios.values():
        case = {
            "scenario_id": scenario["id"],
            "request": scenario["request"],
            "context": scenario["context"],
        }
        if "resolved" in scenario:
            case["resolved"] = scenario["resolved"]
        cases.append(case)
    return cases


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
    if not _ordered(call_names, expected["required_call_order"]):
        failures.append("required_call_order")
    if set(call_names).intersection(expected["forbidden_calls"]):
        failures.append("forbidden_call")

    source = scenario["source"]
    if source == "primary" and "handoff" in scenario:
        listings = [call for call in calls if call.get("name") == "list_motion_assets"]
        if not listings or listings[0].get("arguments") != {"project_id": scenario["handoff"]["project_id"]}:
            failures.append("discovery_listing")
        gets = [call for call in calls if call.get("name") == "get_motion_asset"]
        if "get_motion_asset" in expected["required_call_order"]:
            wanted = {
                "motion_asset_id": scenario["handoff"]["motion_asset_id"],
                "version": scenario["handoff"]["version"],
            }
            if len(gets) != 1 or gets[0].get("arguments") != wanted:
                failures.append("get_exact_pin")
        if "resolve_selection" in call_names:
            failures.append("primary_used_resolver")
    elif source == "legacy":
        if not calls or call_names[0] != "resolve_selection":
            failures.append("legacy_resolve_first")
        elif calls[0].get("arguments", {}).get("selection") != scenario["request"]:
            failures.append("resolve_whole_request")

    missing_reads = set(expected.get("context_reads", [])) - set(trace.get("context_reads", []))
    if missing_reads:
        failures.append("context_reads")

    window = expected.get("window")
    if window is not None:
        if trace.get("window") != window:
            failures.append("window")
        listings = [call for call in calls if call.get("name") == "list_motion_assets"]
        final_listings = [
            call for call in listings
            if call.get("arguments", {}).get("at_ms") == window["at_ms"]
            and call.get("arguments", {}).get("duration_ms") == window["duration_ms"]
        ]
        if expected["route"] != "refuse" and not final_listings:
            failures.append("list_final_window")
        if source == "primary" and expected["route"] != "refuse" and len(listings) < 2:
            failures.append("missing_refresh_listing")

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
            if set(arguments.get("parameters", {})) != set(expected.get("parameter_keys", [])):
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

    serialized = json.dumps(trace, sort_keys=True, ensure_ascii=False)
    if any(term in serialized for term in expected["forbidden_literals"]):
        failures.append("demo_leakage")
    if "cutout_windows" in expected and expected["cutout_windows"] != trace.get("cutout_windows"):
        failures.append("cutout_windows")
    if expected["requires_page_url"] and (not trace.get("page_url") or trace.get("agent_page_url")):
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
        print(json.dumps(model_cases(scenarios), indent=2, ensure_ascii=False))
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

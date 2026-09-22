"""Validate Motion Library discovery and observable adaptation scenarios."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip/references/handoff.md"
ENTRY_SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"
EVALUATOR = ROOT / "tests/fixtures/motion-handoff/evaluate.py"

SPEC = importlib.util.spec_from_file_location("motion_handoff_evaluate", EVALUATOR)
assert SPEC and SPEC.loader
motion_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motion_eval)


def passing_trace(scenario: dict) -> dict:
    expected = scenario["expected"]
    resolved_reference = scenario["resolved"]["references"][0]
    frame_calls = iter(
        scenario["context"].get("listing_entry", {})
        .get("next_data", {})
        .get("cutout", {})
        .get("frame_speaker_calls", [])
    )
    calls = []
    for name in expected["required_call_order"]:
        arguments = {}
        if name == "resolve_selection":
            arguments["selection"] = scenario["request"]
        if name == "list_motion_assets":
            arguments.update(expected.get("window", {}))
        if name == "frame_speaker":
            arguments.update(next(frame_calls))
        if name == "materialize_motion_asset":
            window = expected["window"]
            arguments.update(
                {
                    "timeline_in_ms": window["at_ms"],
                    "duration_ms": window["duration_ms"],
                    "expected_project_revision": scenario["context"]["listing_project_revision"],
                    "parameters": {key: f"grounded-{key}" for key in expected["parameter_keys"]},
                }
            )
            if "media_inputs" in expected:
                arguments["media_inputs"] = expected["media_inputs"]
        calls.append({"name": name, "arguments": arguments})
    return {
        "scenario_id": scenario["id"],
        "route": expected["route"],
        "context_reads": expected.get("context_reads", []),
        "window": expected.get("window"),
        "calls": calls,
        "questions": ["What exact value and unit should the card show?"]
        * expected.get("min_questions", 0),
        "grounded_values": {"labels": ["invite", "activate", "retain"]}
        if expected["requires_grounded_values"]
        else {},
        "cutout_windows": expected.get("cutout_windows"),
        "refused": expected["refused"],
        "page_url": "https://example.invalid/project"
        if expected["requires_page_url"]
        else None,
    }


class HandoffSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.entry = ENTRY_SKILL.read_text(encoding="utf-8")
        cls.scenarios = motion_eval.load_scenarios()

    def test_entry_skill_discovers_a_friendly_reference_without_requiring_legacy_marker(self) -> None:
        description = re.search(r"^description:\s*(.+)$", self.entry, re.MULTILINE).group(1)
        self.assertIn("Motion Library template from a reference link", description)
        self.assertNotIn("@aip", description)
        targeted = self.entry.split("## Targeted changes to an existing project", 1)[1].split("## ", 1)[0]
        self.assertIn("references/handoff.md", targeted)
        self.assertIn("Do not upload the source again", targeted)
        self.assertIn("Legacy Motion Library references", targeted)
        self.assertNotIn("@aip", self.entry)

    def test_reference_documents_the_resolver_wire_without_confusing_playhead_and_target(self) -> None:
        for field in (
            '`kind: "motion_asset"`',
            '`kind: "motion-asset"`',
            "`reference_id`",
            "`expires_at`",
            "`intent`",
            "`placement`",
            "`context`",
        ):
            self.assertIn(field, self.skill)
        self.assertIn("reference's compatibility `at_ms` is null", self.skill)
        self.assertIn("that playhead is context, not an instruction", self.skill)
        self.assertIn("`next_data.cutout.frame_speaker_calls`", self.skill)
        self.assertIn('`storage: "parameter"`', self.skill)
        self.assertIn("unbound or uses overlay storage", self.skill)

    def test_scenario_bank_covers_baseline_conflicts_and_compatibility(self) -> None:
        required = {
            "parameter-adaptation-auto",
            "explicit-time-overrides-playhead",
            "hardcoded-content-derivation",
            "data-template-without-facts",
            "cutout-across-two-kept-spans",
            "explicit-unchanged-direct",
            "retired-reference-refusal",
            "legacy-reference-here",
        }
        self.assertEqual(required, set(self.scenarios))
        for scenario in self.scenarios.values():
            self.assertTrue(scenario["baseline_outcome"])

    def test_model_cases_do_not_leak_baseline_or_candidate_answer(self) -> None:
        cases = motion_eval.model_cases(self.scenarios)
        self.assertEqual(set(self.scenarios), {case["scenario_id"] for case in cases})
        for case in cases:
            self.assertNotIn("baseline_outcome", case)
            self.assertNotIn("expected", case)

    def test_candidate_set_requires_every_scenario_exactly_once(self) -> None:
        traces = [passing_trace(scenario) for scenario in self.scenarios.values()]
        self.assertEqual([], motion_eval.trace_set_failures(self.scenarios, traces))
        self.assertTrue(motion_eval.trace_set_failures(self.scenarios, []))
        duplicate = traces + [traces[0]]
        self.assertIn(
            f"duplicate:{traces[0]['scenario_id']}",
            motion_eval.trace_set_failures(self.scenarios, duplicate),
        )

    def test_canonical_synthetic_traces_satisfy_each_scenario(self) -> None:
        for scenario in self.scenarios.values():
            with self.subTest(scenario=scenario["id"]):
                self.assertEqual([], motion_eval.evaluate(scenario, passing_trace(scenario)))

    def test_evaluator_rejects_incidental_playhead_as_auto_target(self) -> None:
        scenario = self.scenarios["parameter-adaptation-auto"]
        trace = passing_trace(scenario)
        trace["window"] = {"at_ms": 62000, "duration_ms": 6000}
        listing = next(call for call in trace["calls"] if call["name"] == "list_motion_assets")
        listing["arguments"]["at_ms"] = 62000
        failures = motion_eval.evaluate(scenario, trace)
        self.assertIn("window", failures)
        self.assertIn("list_final_window", failures)

    def test_evaluator_rejects_demo_leakage_and_unnecessary_intake(self) -> None:
        scenario = self.scenarios["hardcoded-content-derivation"]
        trace = passing_trace(scenario)
        trace["grounded_values"] = {"heading": "Cats versus dogs"}
        trace["calls"].append({"name": "start_transcribe_project", "arguments": {}})
        failures = motion_eval.evaluate(scenario, trace)
        self.assertIn("demo_leakage", failures)
        self.assertIn("forbidden_call", failures)

    def test_evaluator_rejects_one_cutout_window_bridging_two_takes(self) -> None:
        scenario = self.scenarios["cutout-across-two-kept-spans"]
        trace = passing_trace(scenario)
        trace["cutout_windows"] = [[12000, 18000]]
        frame_call = next(call for call in trace["calls"] if call["name"] == "frame_speaker")
        frame_call["arguments"] = {"start_ms": 12000, "end_ms": 18000}
        materialize = next(call for call in trace["calls"] if call["name"] == "materialize_motion_asset")
        materialize["arguments"]["media_inputs"] = {"speaker": [{"cutout_segments": [[12000, 18000]]}]}
        failures = motion_eval.evaluate(scenario, trace)
        self.assertIn("cutout_windows", failures)
        self.assertIn("frame_speaker_calls", failures)
        self.assertIn("materialize_media_inputs", failures)

    def test_evaluator_requires_one_question_instead_of_inventing_a_fact(self) -> None:
        scenario = self.scenarios["data-template-without-facts"]
        trace = passing_trace(scenario)
        trace["questions"] = []
        trace["route"] = "materialize"
        trace["calls"].append({"name": "materialize_motion_asset", "arguments": {}})
        trace["grounded_values"] = {"metric": "73 percent"}
        failures = motion_eval.evaluate(scenario, trace)
        self.assertIn("too_few_questions", failures)
        self.assertIn("forbidden_call", failures)
        self.assertIn("demo_leakage", failures)

    def test_evaluator_requires_durable_page_url(self) -> None:
        scenario = self.scenarios["explicit-unchanged-direct"]
        trace = passing_trace(scenario)
        trace["page_url"] = None
        trace["agent_page_url"] = "https://example.invalid/embedded"
        self.assertIn("durable_page_url", motion_eval.evaluate(scenario, trace))

    def test_evaluator_rejects_binding_tokens_and_incomplete_materialize_window(self) -> None:
        scenario = self.scenarios["parameter-adaptation-auto"]
        trace = passing_trace(scenario)
        call = next(call for call in trace["calls"] if call["name"] == "materialize_motion_asset")
        call["arguments"]["parameters"] = {
            "{{PARAM_STAGE_1}}": "invite",
            "{{PARAM_STAGE_2}}": "activate",
            "{{PARAM_STAGE_3}}": "retain",
        }
        call["arguments"].pop("duration_ms")
        call["arguments"]["expected_project_revision"] = 13
        failures = motion_eval.evaluate(scenario, trace)
        self.assertIn("materialize_parameter_keys", failures)
        self.assertIn("materialize_window", failures)
        self.assertIn("materialize_revision", failures)


if __name__ == "__main__":
    unittest.main()

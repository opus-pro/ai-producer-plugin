"""Validate Motion Library plain-text handoff and observable adaptation scenarios."""
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
    handoff = scenario.get("handoff", {})
    list_count = 0
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
            arguments["selection"] = scenario["legacy_selection"]
        elif name == "list_motion_assets":
            list_count += 1
            arguments["project_id"] = handoff["project_id"]
            is_final = scenario["source"] == "legacy" or list_count > 1
            if is_final:
                arguments.update(expected.get("window", {}))
        elif name == "get_motion_asset":
            arguments = {
                "motion_asset_id": handoff["motion_asset_id"],
                "version": handoff["version"],
            }
        elif name == "frame_speaker":
            arguments.update(next(frame_calls))
        elif name == "materialize_motion_asset":
            window = expected["window"]
            arguments = {
                "timeline_in_ms": window["at_ms"],
                "duration_ms": window["duration_ms"],
                "expected_project_revision": scenario["context"]["listing_project_revision"],
                "parameters": {key: f"grounded-{key}" for key in expected.get("parameter_keys", [])},
            }
            if "media_inputs" in expected:
                arguments["media_inputs"] = expected["media_inputs"]
        calls.append({"name": name, "arguments": arguments})
    question = "What exact result value and unit should Metric Focus show?"
    if scenario["id"] == "ambiguous-primary-context":
        question = "Which exact project and template context should I use?"
    return {
        "scenario_id": scenario["id"],
        "route": expected["route"],
        "context_reads": expected.get("context_reads", []),
        "window": expected.get("window"),
        "calls": calls,
        "questions": [question] * expected.get("min_questions", 0),
        "grounded_values": {"headline": "A focused workflow speeds review"}
        if expected["requires_grounded_values"]
        else {},
        "cutout_windows": expected.get("cutout_windows"),
        "refused": expected["refused"],
        "page_url": "https://example.invalid/project" if expected["requires_page_url"] else None,
    }


class HandoffSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.entry = ENTRY_SKILL.read_text(encoding="utf-8")
        cls.scenarios = motion_eval.load_scenarios()

    def test_entry_skill_discovers_named_template_context_without_a_reference_url(self) -> None:
        description = re.search(r"^description:\s*(.+)$", self.entry, re.MULTILINE).group(1)
        self.assertIn("named Motion Library template", description)
        self.assertNotIn("reference link", description)
        targeted = self.entry.split("## Targeted changes to an existing project", 1)[1].split("## ", 1)[0]
        self.assertIn("`Project` and `Template` context line", targeted)
        self.assertIn("references/handoff.md", targeted)
        self.assertIn("Do not upload the source again", targeted)

    def test_primary_example_is_exact_plain_text_and_accepts_localized_labels(self) -> None:
        self.assertIn(
            'Use AI Producer to adapt the "Hero Statement" template to this video\'s content and place it where it fits best.\nProject: DEMO_PROJECT | Template: text-hero-statement@4.0.0',
            self.skill,
        )
        self.assertIn("Chinese labels `项目` and `模板`", self.skill)
        self.assertIn("ASCII or full-width colons", self.skill)
        self.assertIn("pipe or middle dot separator", self.skill)
        self.assertIn("optional matching code backticks", self.skill)
        self.assertIn("generic request about a project", self.skill)
        primary = self.skill.split("## Ground and place the primary handoff", 1)[1].split("## ", 1)[0]
        self.assertNotIn("/r/", primary)
        self.assertIn("never goes to `resolve_selection`", primary)
        chinese = self.scenarios["chinese-primary-backticks-derived"]["request"]
        self.assertIn("项目：`DEMO_PROJECT` · 模板：`text-hero-statement@4.0.0`", chinese)

    def test_primary_discovers_then_reads_pin_before_final_window_refresh(self) -> None:
        primary = self.skill.split("## Ground and place the primary handoff", 1)[1].split("## ", 1)[0]
        discover = primary.index("Call `list_motion_assets` with the parsed `project_id` and no invented placement")
        read_pin = primary.index("Call `get_motion_asset`")
        refresh = primary.index("Call `list_motion_assets` again")
        self.assertLess(discover, read_pin)
        self.assertLess(read_pin, refresh)
        self.assertIn("duration bounds", primary)
        self.assertIn("do not execute a cutout plan", primary)
        self.assertIn("different offered version is unavailable", primary)

    def test_grounding_binding_and_derivation_contract_is_preserved(self) -> None:
        primary = self.skill.split("## Ground and place the primary handoff", 1)[1].split("## ", 1)[0]
        self.assertIn("accepted video and media, transcript, saved edit, output timeline", primary)
        self.assertIn("Never leave demo copy", primary)
        self.assertIn('`storage: "parameter"`', primary)
        self.assertIn("exact `key`, never under `binding.token`", primary)
        self.assertIn("unbound semantic slot, overlay storage", primary)
        self.assertIn("smallest necessary derived-composition path", primary)
        self.assertIn("explicit unchanged insertion uses the package defaults", primary)

    def test_cutout_geometry_shape_remains_exact(self) -> None:
        cutout = self.skill.split("## Cutout packages", 1)[1].split("## ", 1)[0]
        self.assertIn("`next_data.cutout.frame_speaker_calls`", cutout)
        self.assertIn("never bridge two takes with one matte", cutout)
        self.assertIn("`media_inputs[input_key]`", cutout)
        self.assertIn("`geometry.object_position`", cutout)
        self.assertIn("never put `object_position` or a `cutout` object at the segment's top level", cutout)
        self.assertIn("tile the final effect window without a gap or overlap", cutout)
        self.assertIn("do not materialize a partial set", cutout)
        self.assertIn("Never silently move an explicit user-selected window", cutout)
        self.assertIn("re-run `frame_speaker` only for spans that moved", cutout)

    def test_only_legacy_marker_uses_resolver(self) -> None:
        legacy = self.skill.split("## Legacy `@aip` compatibility", 1)[1].split("## ", 1)[0]
        self.assertIn("Only a legacy line that starts with `@aip` goes to `resolve_selection`", legacy)
        self.assertIn("`selection` set to that line verbatim", legacy)
        self.assertIn("never under a `request` argument", legacy)
        self.assertIn("Preserve its explicit \"here\" time", legacy)
        self.assertIn("Do not require `get_motion_asset` for an explicit unchanged legacy placement", legacy)

    def test_scenario_bank_covers_required_primary_and_compatibility_cases(self) -> None:
        required = {
            "english-primary-auto",
            "chinese-primary-backticks-derived",
            "explicit-time-and-scope",
            "ambiguous-primary-context",
            "exact-version-unavailable",
            "missing-grounded-fact",
            "cutout-split-spans",
            "cutout-failed-span-refusal",
            "legacy-reference-here",
            "generic-project-request",
        }
        self.assertEqual(required, set(self.scenarios))
        self.assertTrue(all(scenario["contract_intent"] for scenario in self.scenarios.values()))

    def test_model_cases_do_not_leak_contract_intent_parsed_identity_or_expected_answer(self) -> None:
        cases = motion_eval.model_cases(self.scenarios)
        self.assertEqual(set(self.scenarios), {case["scenario_id"] for case in cases})
        for case in cases:
            self.assertNotIn("contract_intent", case)
            self.assertNotIn("handoff", case)
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

    def test_evaluator_rejects_primary_resolver_and_missing_final_refresh(self) -> None:
        scenario = self.scenarios["english-primary-auto"]
        trace = passing_trace(scenario)
        trace["calls"].insert(0, {"name": "resolve_selection", "arguments": {"selection": scenario["request"]}})
        trace["calls"] = [
            call
            for index, call in enumerate(trace["calls"])
            if not (call["name"] == "list_motion_assets" and index > 2)
        ]
        failures = motion_eval.evaluate(scenario, trace)
        self.assertIn("forbidden_call", failures)
        self.assertIn("primary_used_resolver", failures)
        self.assertIn("list_final_window", failures)
        self.assertIn("missing_refresh_listing", failures)

    def test_evaluator_rejects_binding_token_and_wrong_version_source(self) -> None:
        scenario = self.scenarios["english-primary-auto"]
        trace = passing_trace(scenario)
        get_call = next(call for call in trace["calls"] if call["name"] == "get_motion_asset")
        get_call["arguments"]["version"] = "4.1.0"
        materialize = next(call for call in trace["calls"] if call["name"] == "materialize_motion_asset")
        materialize["arguments"]["parameters"] = {"{{PARAM_HEADLINE}}": "grounded"}
        failures = motion_eval.evaluate(scenario, trace)
        self.assertIn("get_exact_pin", failures)
        self.assertIn("materialize_parameter_keys", failures)

    def test_evaluator_rejects_calls_for_ambiguous_or_generic_requests(self) -> None:
        for scenario_id in ("ambiguous-primary-context", "generic-project-request"):
            scenario = self.scenarios[scenario_id]
            trace = passing_trace(scenario)
            trace["calls"].append({"name": "list_motion_assets", "arguments": {"project_id": "DEMO"}})
            self.assertIn("forbidden_call", motion_eval.evaluate(scenario, trace))

    def test_evaluator_preserves_explicit_time_and_rejects_demo_leakage(self) -> None:
        explicit = self.scenarios["explicit-time-and-scope"]
        trace = passing_trace(explicit)
        trace["window"] = {"at_ms": 22000, "duration_ms": 4000}
        self.assertIn("window", motion_eval.evaluate(explicit, trace))

        missing_fact = self.scenarios["missing-grounded-fact"]
        trace = passing_trace(missing_fact)
        trace["grounded_values"] = {"metric": "73%"}
        self.assertIn("demo_leakage", motion_eval.evaluate(missing_fact, trace))

    def test_missing_fact_accepts_one_plain_question_without_mutation(self) -> None:
        scenario = self.scenarios["missing-grounded-fact"]
        trace = passing_trace(scenario)
        self.assertEqual([], motion_eval.evaluate(scenario, trace))
        self.assertNotIn("materialize_motion_asset", [call["name"] for call in trace["calls"]])
        self.assertNotIn("commit_workspace", [call["name"] for call in trace["calls"]])

    def test_unavailable_pin_stops_without_a_substitution_question(self) -> None:
        scenario = self.scenarios["exact-version-unavailable"]
        trace = passing_trace(scenario)
        trace["questions"] = ["Would you like to use version 1.3.0 instead?"]
        self.assertIn("too_many_questions", motion_eval.evaluate(scenario, trace))

    def test_legacy_resolver_uses_selection_with_only_the_marker_line(self) -> None:
        scenario = self.scenarios["legacy-reference-here"]
        trace = passing_trace(scenario)
        resolve = trace["calls"][0]
        resolve["arguments"] = {"request": scenario["legacy_selection"]}
        self.assertIn("resolve_marker_line", motion_eval.evaluate(scenario, trace))

    def test_evaluator_rejects_one_cutout_window_bridging_two_takes(self) -> None:
        scenario = self.scenarios["cutout-split-spans"]
        trace = passing_trace(scenario)
        trace["cutout_windows"] = [[12000, 18000]]
        frame_call = next(call for call in trace["calls"] if call["name"] == "frame_speaker")
        frame_call["arguments"] = {"project_id": "DEMO_CUTOUT", "windows": []}
        materialize = next(call for call in trace["calls"] if call["name"] == "materialize_motion_asset")
        materialize["arguments"]["media_inputs"] = {"speaker": [{"start_ms": 12000, "end_ms": 18000}]}
        failures = motion_eval.evaluate(scenario, trace)
        self.assertIn("cutout_windows", failures)
        self.assertIn("frame_speaker_calls", failures)
        self.assertIn("materialize_media_inputs", failures)

    def test_evaluator_refuses_partial_cutout_after_one_failed_span(self) -> None:
        scenario = self.scenarios["cutout-failed-span-refusal"]
        trace = passing_trace(scenario)
        self.assertEqual([], motion_eval.evaluate(scenario, trace))
        trace["calls"].append(
            {
                "name": "materialize_motion_asset",
                "arguments": {
                    "timeline_in_ms": 12000,
                    "duration_ms": 6000,
                    "expected_project_revision": 22,
                    "parameters": {},
                    "media_inputs": {
                        "speaker": [
                            {
                                "path": "render-engine/public/span-1.webm",
                                "start_ms": 12000,
                                "end_ms": 14500,
                            }
                        ]
                    },
                },
            }
        )
        self.assertIn("forbidden_call", motion_eval.evaluate(scenario, trace))


if __name__ == "__main__":
    unittest.main()

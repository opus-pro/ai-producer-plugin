from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".agents/skills/aip-plugin-local"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, WORKFLOW / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_script("build_local")
cost = load_script("cost_report")


class LocalPackageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.output = self.root / "local-marketplace"

    def tearDown(self):
        self.temp.cleanup()

    def test_build_preserves_source_and_refreshes_both_hosts(self):
        original = builder.files(REPO / "plugins/aip")
        first = builder.build(REPO, self.output)
        second = builder.build(REPO, self.output)
        self.assertNotEqual(first["version"], second["version"])
        self.assertEqual(original, builder.files(REPO / "plugins/aip"))
        self.assertEqual(original, second["source_files"])
        plugin = self.output / "plugins/aip"
        codex = builder.read_json(plugin / ".codex-plugin/plugin.json")
        claude = builder.read_json(plugin / ".claude-plugin/plugin.json")
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["interface"]["displayName"], "AI Producer Local")
        self.assertEqual(codex["interface"]["composerIcon"], "./assets/local.svg")
        self.assertEqual((plugin / "assets/local.svg").read_bytes(), (WORKFLOW / "assets/local.svg").read_bytes())
        self.assertFalse((plugin / "skills/aip-plugin-local").exists())
        config = builder.read_json(plugin / ".mcp.json")["mcpServers"]["aip"]
        for host in ("headers", "http_headers"):
            self.assertEqual(config[host][builder.VERSION_HEADER], second["version"])
        marketplace = builder.read_json(self.output / ".claude-plugin/marketplace.json")
        self.assertEqual(marketplace["plugins"][0]["version"], second["version"])
        for relative in original:
            if relative.startswith(("skills/", "licenses/")) or "LICENSE" in relative or "NOTICES" in relative:
                self.assertEqual((plugin / relative).read_bytes(), (REPO / "plugins/aip" / relative).read_bytes())

    def test_cache_verification_catches_stale_and_extra_files(self):
        builder.build(REPO, self.output)
        cache = self.root / "cache"
        shutil.copytree(self.output / "plugins/aip", cache)
        self.assertTrue(builder.verify(self.output, cache)["verified"])
        (cache / "unexpected.txt").write_text("stale cached file")
        with self.assertRaisesRegex(ValueError, "cache"):
            builder.verify(self.output, cache)

    def test_unowned_or_edited_output_is_not_destroyed(self):
        self.output.mkdir()
        user_file = self.output / "keep.txt"
        user_file.write_text("keep me")
        with self.assertRaisesRegex(ValueError, "not owned"):
            builder.build(REPO, self.output)
        self.assertEqual(user_file.read_text(), "keep me")
        user_file.unlink()
        self.output.rmdir()
        builder.build(REPO, self.output)
        user_file.write_text("keep this too")
        with self.assertRaisesRegex(ValueError, "was edited"):
            builder.build(REPO, self.output)
        self.assertTrue(user_file.exists())

    def test_explicit_endpoint_updates_oauth_and_rejects_credentials(self):
        result = builder.build(REPO, self.output, "http://localhost:8123/api/mcp")
        config = builder.read_json(self.output / "plugins/aip/.mcp.json")["mcpServers"]["aip"]
        self.assertEqual(config["url"], config["oauth_resource"])
        self.assertEqual(result["mcp_url"], config["url"])
        for value in ("http://remote.example/api/mcp", "https://user:pass@example.com/mcp", "https://example.com/mcp?token=x"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                builder.endpoint(value)

    def test_output_symlink_is_not_followed(self):
        target = self.root / "untouched"
        target.mkdir()
        self.output.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            builder.build(REPO, self.output)
        self.assertEqual(list(target.iterdir()), [])


ROOT_ID = "00000000-0000-0000-0000-000000000001"
CHILD_ID = "00000000-0000-0000-0000-000000000002"
RATES = {
    "source": "https://developers.openai.com/", "verified_on": "2026-01-01",
    "models": {"example-model": {"tier": "standard", "input": 10, "cached": 1, "output": 50,
        "long_context": {"threshold": 272000, "input_multiplier": 2, "cached_multiplier": 2, "output_multiplier": 1.5}}},
}


def usage(input_tokens=100, cached=80, output=10):
    return {"input_tokens": input_tokens, "cached_input_tokens": cached, "cache_write_input_tokens": 0,
            "output_tokens": output, "reasoning_output_tokens": 3, "total_tokens": input_tokens + output}


def event(kind, payload):
    return {"type": kind, "payload": payload}


def record(owner, number, tokens, cumulative=None):
    return event("token_usage_record", {"thread_id": owner, "turn_id": owner, "root_turn_id": ROOT_ID,
        "response_id": f"{owner}-{number}", "usage": tokens, "thread_token_usage": cumulative or tokens})


class ClientCostTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_session(self, identifier, records, parent=None, complete=True):
        source = {"subagent": {"thread_spawn": {"parent_thread_id": parent}}} if parent else "cli"
        rows = [event("session_meta", {"id": identifier, "source": source}),
                event("turn_context", {"turn_id": identifier, "model": "example-model", "service_tier": None})]
        rows += records
        if complete:
            rows.append(event("event_msg", {"type": "task_complete", "turn_id": identifier, "duration_ms": 1000,
                                           "last_agent_message": "PRIVATE TEXT MUST NOT BE EXPORTED"}))
        path = self.root / f"{identifier}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        return path

    def test_forked_history_and_duplicate_receipts_do_not_double_count(self):
        parent_record = record(ROOT_ID, 1, usage())
        self.write_session(ROOT_ID, [parent_record, parent_record])
        self.write_session(CHILD_ID, [parent_record, record(CHILD_ID, 1, usage(50, 0, 5))], parent=ROOT_ID)
        report = cost.report(ROOT_ID, self.root, RATES)
        self.assertEqual(report["responses"], 2)
        self.assertEqual(report["tokens"]["input_tokens"], 150)
        self.assertEqual(report["tokens"]["output_tokens"], 15)
        self.assertAlmostEqual(report["usd"], 0.00153)
        self.assertEqual(report["elapsed_ms"], 1000)
        self.assertNotIn("PRIVATE TEXT", json.dumps(report))

    def test_long_context_pricing_is_per_response(self):
        short = usage(200000, 100000, 10)
        self.assertAlmostEqual(cost.price(short, {"model": "example-model"}, RATES)[0], 1.1005)
        long = usage(300000, 100000, 10)
        self.assertAlmostEqual(cost.price(long, {"model": "example-model"}, RATES)[0], 4.20075)

    def test_missing_rates_or_cache_write_usage_is_unknown_not_zero(self):
        self.write_session(ROOT_ID, [record(ROOT_ID, 1, usage())])
        self.assertIsNone(cost.report(ROOT_ID, self.root)["usd"])
        changed = usage()
        changed["cache_write_input_tokens"] = 10
        self.assertIsNone(cost.price(changed, {"model": "example-model"}, RATES)[0])
        self.assertIsNone(cost.price(usage(), {"model": "example-model", "service_tier": "priority"}, RATES)[0])

    def test_missing_receipt_prevents_complete_cost_total(self):
        self.write_session(ROOT_ID, [record(ROOT_ID, 2, usage(), usage(200, 160, 20))])
        result = cost.report(ROOT_ID, self.root, RATES)
        self.assertFalse(result["threads"][0]["reconciled"])
        self.assertIsNone(result["usd"])

    def test_running_partial_file_is_labeled_as_snapshot(self):
        path = self.write_session(ROOT_ID, [record(ROOT_ID, 1, usage())], complete=False)
        with path.open("a") as stream:
            stream.write('{"type":')
        result = cost.report(ROOT_ID, self.root, RATES)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["elapsed_ms"])
        self.assertTrue(result["threads"][0]["partial_tail"])
        self.assertAlmostEqual(result["usd"], 0.00078)

    def test_other_subagent_metadata_variants_do_not_break_discovery(self):
        self.write_session(ROOT_ID, [record(ROOT_ID, 1, usage())])
        other = event("session_meta", {"id": CHILD_ID, "source": {"subagent": "review"}})
        (self.root / "unrelated.jsonl").write_text(json.dumps(other) + "\n")
        result = cost.report(ROOT_ID, self.root, RATES)
        self.assertEqual(len(result["threads"]), 1)
        self.assertAlmostEqual(result["usd"], 0.00078)

    def test_pending_followup_without_receipts_is_not_complete(self):
        path = self.write_session(ROOT_ID, [record(ROOT_ID, 1, usage())])
        with path.open("a") as stream:
            stream.write(json.dumps(event("event_msg", {"type": "task_started", "turn_id": "followup"})) + "\n")
            stream.write(json.dumps(event("turn_context", {"turn_id": "followup", "model": "example-model"})) + "\n")
        result = cost.report(ROOT_ID, self.root, RATES)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["elapsed_ms"])
        self.assertTrue(result["threads"][0]["issues"])
        generation = cost.report(ROOT_ID, self.root, RATES, ROOT_ID)
        self.assertTrue(generation["complete"])
        self.assertEqual(generation["elapsed_ms"], 1000)

    def test_turn_scope_excludes_followups_and_their_children(self):
        path = self.write_session(ROOT_ID, [record(ROOT_ID, 1, usage())])
        followup = record(ROOT_ID, 2, usage(), {k: v * 2 for k, v in usage().items()})
        followup["payload"].update(turn_id="followup", root_turn_id="followup")
        later = [event("turn_context", {"turn_id": "followup", "model": "example-model"}), followup,
                 event("event_msg", {"type": "task_complete", "turn_id": "followup", "duration_ms": 500})]
        with path.open("a") as stream:
            stream.write("".join(json.dumps(row) + "\n" for row in later))
        inherited_context = event("turn_context", {"turn_id": ROOT_ID, "model": "example-model"})
        self.write_session(CHILD_ID, [inherited_context, record(CHILD_ID, 1, usage())], parent=ROOT_ID)
        other_id = "00000000-0000-0000-0000-000000000003"
        later_child = record(other_id, 1, usage())
        later_child["payload"]["root_turn_id"] = "followup"
        self.write_session(other_id, [later_child], parent=ROOT_ID)
        generation = cost.report(ROOT_ID, self.root, RATES, ROOT_ID)
        self.assertEqual(generation["responses"], 2)
        self.assertEqual(len(generation["threads"]), 2)
        self.assertAlmostEqual(generation["usd"], 0.00156)
        self.assertEqual(generation["elapsed_ms"], 1000)
        self.assertTrue(generation["complete"])
        entire_task = cost.report(ROOT_ID, self.root, RATES)
        self.assertEqual(entire_task["responses"], 4)
        self.assertAlmostEqual(entire_task["usd"], 0.00312)
        self.assertEqual(entire_task["elapsed_ms"], 1500)
        with self.assertRaisesRegex(ValueError, "not present"):
            cost.report(ROOT_ID, self.root, RATES, "absent-turn")

    def test_missing_child_root_turn_is_unknown_in_scoped_report(self):
        self.write_session(ROOT_ID, [record(ROOT_ID, 1, usage())])
        child = record(CHILD_ID, 1, usage())
        child["payload"].pop("root_turn_id")
        self.write_session(CHILD_ID, [child], parent=ROOT_ID)
        result = cost.report(ROOT_ID, self.root, RATES, ROOT_ID)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["usd"])
        self.assertEqual(result["threads"][1]["unassigned_response_count"], 1)
        self.assertAlmostEqual(cost.report(ROOT_ID, self.root, RATES)["usd"], 0.00156)

    def test_direct_child_query_excludes_inherited_context_without_receipt(self):
        self.write_session(ROOT_ID, [record(ROOT_ID, 1, usage())], complete=False)
        inherited = event("turn_context", {"turn_id": ROOT_ID, "model": "example-model"})
        self.write_session(CHILD_ID, [inherited, record(CHILD_ID, 1, usage())], parent=ROOT_ID)
        result = cost.report(CHILD_ID, self.root, RATES)
        self.assertTrue(result["complete"])
        self.assertEqual(result["responses"], 1)
        self.assertEqual(result["elapsed_ms"], 1000)
        self.assertAlmostEqual(result["usd"], 0.00078)


if __name__ == "__main__":
    unittest.main()

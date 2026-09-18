"""Keep the skill's model boundary aligned with visible publication progress."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"
REFERENCE = ROOT / "plugins/aip/skills/aip/references/progressive-publication.md"


class ProgressiveSkillContractTests(unittest.TestCase):
    def test_batch_drafts_can_overlap_but_publications_remain_ordered(self):
        skill = SKILL.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("batches of up to two while the preceding batch publishes", skill)
        self.assertIn("publish each effect in order", skill)
        self.assertIn("publication_batch.js", reference)
        self.assertIn("afterEffect: 0", reference)
        self.assertIn("without claiming overlap", skill)
        self.assertNotIn("before generating any source for the next effect", skill)
        self.assertIn("progressive_checkpoint.py\" init", reference)

    def test_publication_uses_the_current_task_mcp(self):
        skill = SKILL.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("AI Producer MCP tools already loaded in the current task", skill)
        self.assertIn("Call the AI Producer MCP tools already loaded in the current task", reference)
        self.assertNotIn("mcpServer/tool/call", reference)
        self.assertIn("Never run `codex`, start an app server, create an ephemeral task", reference)

    @unittest.skipUnless(shutil.which("node"), "Node is needed only for host-JavaScript tests")
    def test_publication_example_uses_advertised_callable_names(self):
        example = re.search(r"```javascript\n(.*?)\n```", REFERENCE.read_text(), re.DOTALL).group(1)
        harness = r"""
const assert = require("node:assert/strict");
(async () => {
  for (const prefix of ["mcp__ai_producer__", "mcp__ai-producer__", "host_selected_plugin__"]) {
    const publicationToolNames = {
      signUpload: prefix + "sign_workspace_upload",
      commitWorkspace: prefix + "commit_workspace",
      waitTask: prefix + "wait_task",
    };
    const tools = Object.fromEntries(Object.values(publicationToolNames).map(name => [name, () => name]));
    const source = `bindings => {
      for (const key of Object.keys(publicationToolNames)) {
        assert.equal(bindings[key], tools[publicationToolNames[key]]);
        assert.equal(typeof bindings[key], "function");
      }
      return async () => ({ bound: true });
    }`;
    const yield_control = () => {}, text = value => assert.deepEqual(value, { bound: true });
    const aipSkillPath = "skill", renderEnginePath = "workspace", checkpointPath = "checkpoint";
    const draft2Path = "draft2", draft3Path = "draft3";
    await eval("(async () => {" + EXAMPLE + "})()");
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
        result = subprocess.run(
            ["node", "-e", harness.replace("EXAMPLE", json.dumps(example))],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

"""Keep the skill's model boundary aligned with visible publication progress."""
from pathlib import Path
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
        self.assertIn("AIP MCP tools already loaded in the current task", skill)
        self.assertIn("Call the AIP MCP tools already loaded in the current task", reference)
        self.assertNotIn("mcpServer/tool/call", reference)
        self.assertIn("Never run `codex`, start an app server, create an ephemeral task", reference)

if __name__ == "__main__":
    unittest.main()

"""Keep the skill's model boundary aligned with visible publication progress."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"
REFERENCE = ROOT / "plugins/aip/skills/aip/references/progressive-publication.md"


class ProgressiveSkillContractTests(unittest.TestCase):
    def test_each_effect_requires_a_model_checkpoint_after_acceptance(self):
        skill = SKILL.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("before generating any source for the next effect", skill)
        self.assertIn("Only after `accept` returns", reference)
        self.assertIn("progressive_checkpoint.py\" prepare", reference)
        self.assertIn("progressive_checkpoint.py\" accept", reference)

    def test_publication_uses_the_current_task_mcp(self):
        skill = SKILL.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("AIP MCP tools already loaded in the current task", skill)
        self.assertIn("Call the AIP MCP tools already loaded in the current task", reference)
        self.assertNotIn("mcpServer/tool/call", reference)
        self.assertIn("Never run `codex`, start an app server, create an ephemeral task", reference)

    def test_reference_does_not_restore_the_multi_effect_generator_loop(self):
        reference = REFERENCE.read_text(encoding="utf-8")
        self.assertNotIn("for position, beat in enumerate", reference)
        self.assertNotIn("author_one_effect_and_update_index", reference)
        self.assertIn("Do not define a multi-effect authoring function", reference)


if __name__ == "__main__":
    unittest.main()

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



def _fine_cut_section(skill):
    """The fine cut's prose, from its heading to the finishes round."""
    return skill[skill.index("**Fine cut.**"):skill.index("**Finishes.**")]


class FineCutReferenceImageContractTests(unittest.TestCase):
    """The reference image is collected by the card where it can save a file, and asked in words where not."""

    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")
        self.fine_cut = _fine_cut_section(self.skill)

    def test_the_card_no_longer_claims_it_cannot_carry_an_image(self):
        self.assertNotIn("The reference image is not on this card", self.skill)
        self.assertNotIn("a card collects one line of text and an image is a file", self.skill)

    def test_rounds_table_offers_the_image_as_the_cards_own_question(self):
        row = next(line for line in self.skill.splitlines() if line.startswith("| Fine cut |"))
        self.assertIn("`reference_image` where the server offers it", row)
        self.assertIn("`reference_image=<path>` once the image is accepted", row)

    def test_card_upload_is_staged_until_the_commit_round_accepts_it(self):
        self.assertIn("present_choices` given the `project_id` and `reference_image`", self.fine_cut)
        self.assertIn("the card collects the image: do not ask for it in words", self.fine_cut)
        self.assertIn("staged, not yet accepted", self.fine_cut)
        self.assertIn("poll `get_task` on that task id until it reports the file accepted", self.fine_cut)
        self.assertIn(
            "A successful upload, a queued task, or a task that finished without accepting the file is not acceptance.",
            self.fine_cut,
        )
        # Waiting comes before recording, and the recording carries every answer at once.
        self.assertLess(
            self.fine_cut.index("poll `get_task`"),
            self.fine_cut.index("only then record `branding`"),
        )
        self.assertIn("every fine cut answer and `reference_image=<path>` in one `record_choices` call", self.fine_cut)
        self.assertIn("When the round refuses it, record `branding` without the path", self.fine_cut)

    def test_intent_answer_is_never_a_path(self):
        self.assertIn('"I\'ll attach a reference image" is intent, never a path', self.fine_cut)
        self.assertIn("give a local image path you can read, and end the turn", self.fine_cut)
        self.assertIn("`commit_workspace` with `expected_files` bound to that exact path and its sha256", self.fine_cut)
        self.assertIn('"Continue without one" is the skip too', self.fine_cut)

    def test_ask_once_never_after_skip_and_reuse_an_earlier_picture(self):
        self.assertIn("Ask it once for the whole project, and never a second time - not after a skip", self.fine_cut)
        self.assertIn("`reference_image` already recorded under `branding`", self.fine_cut)
        self.assertIn("When they handed a picture over earlier in the conversation, do not ask: use it", self.fine_cut)
        self.assertEqual(self.fine_cut.count("Ask it once for the whole project"), 1)

    def test_card_without_the_question_keeps_the_plain_words_ask(self):
        self.assertIn("the result reports it rejected where it does not; the card then goes up without it", self.fine_cut)
        fallback = self.fine_cut[self.fine_cut.index("When the card does not carry the question"):]
        self.assertIn("before the finishes round goes up, ask them for the picture in plain words", fallback)
        self.assertIn("not a card and not a line inside the note", fallback)
        self.assertIn('"skip" or any other reply: raise the finishes round.', fallback)
        # Hosts with no cards at all still ask it as its own question.
        self.assertIn("the reference image is still asked for as its own question", self.skill)

if __name__ == "__main__":
    unittest.main()

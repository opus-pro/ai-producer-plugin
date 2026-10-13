"""Keep the two settle-before-cutting rounds aligned with the cards the service draws."""
from pathlib import Path
import base64
import hashlib
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"
CAPTION_SKILL = ROOT / "plugins/aip/skills/aip-dynamic-caption/SKILL.md"
CARD_BUNDLE = ROOT / "plugins/aip/assets/decision-card/decision-card.js"

# The service's card options, in the order its cards list them.
ROUGH_CUT_BOLDNESS = ["off", "conservative", "balanced", "aggressive"]
CAPTION_PATTERNS = [
    "blur-ladder",
    "editorial-stack",
    "inverted-stack",
    "lead-in-flare",
    "pace-adaptive",
    "scribble-subtitle",
    "solo-word-punch",
    "tilt-slam",
]
# Fine-cut components the agent never asks for; `editing_preference` is the optional
# "Anything else?" box at the foot of the one card, asked but never followed up.
REFUSED_FINE_CUT_COMPONENTS = [
    "editing_preference_example",
    "reference_image",
    "visual_preference_prompt",
]


def section(text: str, start: str) -> str:
    return text[text.index(start):].split("\n\n", 1)[0]


class RoundsSkillContractTests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")

    def test_only_rough_cut_and_finishes_are_carded(self):
        rows = re.findall(r"^\| (Rough cut|Finishes|Fine cut) \| `(\w+)` \| (.+?) \|", self.skill, re.MULTILINE)
        self.assertEqual(
            [(name, card, re.findall(r"`(\w+)`", components)) for name, card, components in rows],
            [
                ("Rough cut", "roughcut", ["rough_cut_boldness"]),
                ("Finishes", "finishing", ["caption_style", "bgm_enabled", "sfx_enabled"]),
            ],
        )
        self.assertIn("`bgm_enabled=on`, `sfx_enabled=off`", self.skill)

    def test_rough_cut_names_the_four_boldness_values_in_card_order(self):
        rough_cut = section(self.skill, "**Rough cut.**")
        positions = [rough_cut.index(f"`{value}`") for value in ROUGH_CUT_BOLDNESS]
        self.assertEqual(positions, sorted(positions))

    def test_finishes_offers_no_caption_and_the_service_patterns(self):
        self.assertIn("`no-caption` (\"No captions\") and eight caption patterns", self.skill)
        rows = re.findall(r"^\|[^|]+\| `([a-z-]+)`\s+\|", CAPTION_SKILL.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertEqual(rows, CAPTION_PATTERNS)

    def test_fine_cut_components_are_refused_even_when_offered(self):
        fine_cut = section(self.skill, "**Fine cut.**")
        self.assertIn("The fine cut is not a round.", fine_cut)
        self.assertIn("even when `present_choices` offers components for them", fine_cut)
        refused = fine_cut[fine_cut.index("Do not ask"):fine_cut.index("The user's own words outrank")]
        for component in REFUSED_FINE_CUT_COMPONENTS:
            self.assertIn(f"`{component}`", refused)
        self.assertNotIn("`editing_preference`", refused)
        self.assertIn("styling reference for palette and type; use it without asking for one or recording it", fine_cut)

    def test_open_rounds_are_asked_on_one_card_and_recorded_apart(self):
        self.assertIn("Ask every round still open at once, on one card, in the order they are listed.", self.skill)
        self.assertIn("two separate decisions with a record each; they are only asked together", self.skill)
        self.assertNotIn("one at a time", self.skill)
        self.assertNotIn("raise the next round", self.skill)
        rounds = section(self.skill, "All open rounds go on one card")
        self.assertIn("call `present_choices` with the components of every round still open, in table order, then `editing_preference` last", rounds)
        self.assertIn("A round the opening settled puts none of its components on the card.", rounds)
        self.assertIn("one `record_choices` per round it asked: the rough-cut answer under `roughcut` and the finishing answers under `finishing`", rounds)

    def test_anything_else_box_is_optional_and_never_recorded(self):
        fine_cut = section(self.skill, "**Fine cut.**")
        self.assertIn("the optional \"Anything else?\" box at the foot of the card: the card sends without it, and a blank box is never followed up", fine_cut)
        self.assertIn("`editing_preference=<text>`", fine_cut)
        self.assertIn("record no `branding` entry for it", fine_cut)

    def test_hosts_that_draw_the_card_keep_the_card_flow(self):
        hosts = section(self.skill, "**Hosts that show the card as data.**")
        self.assertIn("Hosts with neither of the two tools named below draw the card: run the rounds as above.", hosts)

    def test_widget_hosts_draw_the_pinned_bundle_as_written(self):
        hosts = section(self.skill, "**Hosts that show the card as data.**")
        self.assertIn(
            "When `show_widget` is among your tools - by that name alone or behind a server prefix, as in Claude Code's `mcp__visualize__show_widget` -",
            hosts,
        )
        self.assertNotIn("named exactly `show_widget`", self.skill, "Claude Code lists the tool with its server prefix")
        script = re.search(
            r'<script src="https://cdn\.jsdelivr\.net/gh/opus-pro/ai-producer-plugin@([0-9a-f]{40})/plugins/aip/assets/decision-card/decision-card\.js" integrity="(sha384-[A-Za-z0-9+/=]+)" crossorigin="anonymous"></script>',
            self.skill,
        )
        self.assertIsNotNone(script, "the widget must load the bundle pinned to a commit, with its integrity")
        assert script is not None
        expected = "sha384-" + base64.b64encode(hashlib.sha384(CARD_BUNDLE.read_bytes()).digest()).decode()
        self.assertEqual(script.group(2), expected, "the pinned integrity must match the bundle this package ships")
        self.assertIn('<script>AIPDecisionCard.render(CARD, { mount: "aip-card", key: "roughcut-1" })</script>', self.skill)
        short_card = section(self.skill, "`CARD` is ")
        self.assertIn("each component it served by its id alone", short_card)
        self.assertIn("`displays` true when its result's components carry a `display` field", short_card)
        self.assertIn("Never copy the result's options or descriptions into the widget", short_card)
        self.assertIn(
            "A server prefix does not make it a different tool, but a tool with another name, however similar its name or purpose, does not stand in for `show_widget`",
            self.skill,
        )

    def test_skill_descriptions_are_english_and_route_any_language(self):
        # Hosts show a skill's description in their menus, so it stays English; the
        # "in any language" clause is what routes a request written in another one.
        for skill in sorted((ROOT / "plugins/aip/skills").glob("*/SKILL.md")):
            description = re.search(r"^description:\s*(.+)$", skill.read_text(encoding="utf-8"), re.MULTILINE).group(1)
            self.assertTrue(description.isascii(), skill)
        entry = re.search(r"^description:\s*(.+)$", self.skill, re.MULTILINE).group(1)
        self.assertIn("in any language", entry)
        for capability in ("cut or edit", "captions or subtitles", "motion graphics", "background music", "inserted images or video clips", "export"):
            self.assertIn(capability, entry)

    def test_first_round_goes_up_while_the_source_uploads(self):
        preparing = section(self.skill, "Preparing the project is not editing")
        self.assertNotIn("Only then read the saved default", preparing)
        self.assertLess(preparing.index("`sign_upload`"), preparing.index("put up the card"))
        self.assertLess(preparing.index("put up the card"), preparing.index("The moment the PUT finishes, call `start_transcribe_project`"))
        self.assertIn("keep the turn until the upload has finished and preparation has started", preparing)
        self.assertIn("a question tool that waits for the answer", preparing)
        self.assertIn("[upload_batch.py](scripts/upload_batch.py) given the source's folder as its root", preparing)
        # The conversation without a computer still signs nothing.
        self.assertIn("A conversation with no computer behind it, which Known issues below covers: nothing is signed there.", preparing)
        price = section(self.skill, "Preparation spends")
        self.assertIn("`get_pricing`, without a project", price)
        self.assertIn("the message that raises the card", price)

    def test_answers_before_the_project_are_held_then_recorded(self):
        rounds = section(self.skill, "All open rounds go on one card")
        self.assertNotIn("Preparation is already under way by the first card", rounds)
        self.assertIn("is held in the conversation as given, the latest answer for each round", rounds)
        self.assertIn("written down under its card id as soon as the project is created", rounds)
        self.assertIn("When the card is answered before the project exists, let the upload finish, start preparation, write the held answers", rounds)
        widget = section(self.skill, "The card's Send puts the answer")
        self.assertIn("end your turn once preparation has started", widget)

    def test_terminal_hosts_ask_each_round_without_the_card(self):
        terminal = section(self.skill, "Without `show_widget` under any prefix, a host whose tools include one named exactly `AskUserQuestion`")
        self.assertIn("so do not call `present_choices` there", terminal)
        self.assertIn("ask every open round in one `AskUserQuestion` call", terminal)
        self.assertIn("at most four questions, which the two rounds fill exactly", terminal)
        self.assertIn("at most four options each", terminal)
        self.assertIn("letting the run choose, which records no `caption_style`", terminal)
        self.assertIn("Write down the token each chosen option stands for, never the label the user saw.", terminal)

    def test_hosts_without_cards_ask_the_open_rounds_in_one_message(self):
        plain = section(self.skill, "Not every install has the cards.")
        self.assertIn("every still-open round in one message, each as a question of its own", plain)
        self.assertNotIn("one round per turn", plain)


if __name__ == "__main__":
    unittest.main()

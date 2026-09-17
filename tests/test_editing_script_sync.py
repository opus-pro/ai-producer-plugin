"""Synthetic cut/document parity checks; no media, credentials, or hosted calls."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts/editing_script_sync.py"
SPEC = importlib.util.spec_from_file_location("editing_script_sync", SCRIPT)
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


def word(identifier, start, end, **extra):
    return {"id": identifier, "text": identifier, "srcStart": start, "srcEnd": end,
            "timelineIn": start, "timelineOut": end, **extra}


def segment(identifier, words, start=0, end=6000):
    return {"id": identifier, "cueType": "subtitle", "words": words,
            "timelineIn": start, "timelineOut": end}


def document(words=None):
    words = words if words is not None else [word("w-1", 1000, 1500), word("w-4", 4000, 4500)]
    return {"schemaVersion": 1, "rev": 3,
            "source": {"path": "public/source.mp4", "duration": 6000},
            "tracks": [
                {"id": "t-av", "type": "av", "speakerVolume": 0.8, "items": [
                    {"id": "clip-0", "srcStart": 0, "srcEnd": 6000, "timelineIn": 0, "timelineOut": 6000}]},
                {"id": "t-captions", "type": "captions", "items": [
                    {"id": "section-0", "kind": "paragraph", "segments": [segment("phrase-0", words)]}]},
            ]}


def index(spans=((0, 6),), split=False, extra="", source="public/source.mp4", audio="public/source.mp3"):
    elements, cursor = [], 0
    for number, (start, duration) in enumerate(spans):
        pair = []
        for tag, key, path in [("video", "speaker", source), ("audio", "speaker-audio", audio)]:
            identifier = key if number == 0 else "{}-{}".format(key, number)
            classes = "clip speaker-clip" if split or len(spans) > 1 else "clip"
            clip_id = ' data-hf-id="clip-{}"'.format(number) if "speaker-clip" in classes else ""
            pair.append('<{} id="{}" class="{}"{} src="{}" data-start="{}" '
                        'data-media-start="{}" data-duration="{}"></{}>'.format(
                            tag, identifier, classes, clip_id, path, cursor, start, duration, tag))
        elements.extend(pair)
        cursor += duration
    return '<div id="stage" data-composition-id="finecut-root" data-start="0" data-duration="{}">{}{}</div>'.format(
        cursor, "".join(elements), extra)


def track(doc, kind):
    return next(item for item in doc["tracks"] if item["type"] == kind)


def words(doc):
    return [item for section in track(doc, "captions")["items"]
            for part in section["segments"] for item in part["words"]]


def span(item):
    return item["timelineIn"], item["timelineOut"]


class EditingScriptSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "compositions").mkdir()
        self.path = self.root / sync.EDITING_SCRIPT

    def write(self, html=None, doc=None):
        (self.root / "index.html").write_text(html or index(), encoding="utf-8")
        self.path.write_text(json.dumps(doc or document()), encoding="utf-8")

    def test_html_only_cut_updates_av_and_each_word_across_one_phrase(self):
        before = document([word("kept-head", 1000, 1500), word("removed", 2500, 2800),
                           word("kept-tail", 4000, 4500)])
        snapshot = deepcopy(before)
        after = sync.synchronize(index(((0, 2), (4, 2))), before)
        self.assertEqual(before, snapshot)
        self.assertEqual(after["rev"], 4)
        playing = sync._playing(track(after, "av"))
        self.assertEqual([(item["srcStart"], item["srcEnd"], *span(item)) for item in playing],
                         [(0, 2000, 0, 2000), (4000, 6000, 2000, 4000)])
        self.assertEqual([span(item) for item in words(after)], [(1000, 1500), (2000, 2000), (2000, 2500)])
        self.assertEqual(track(after, "av")["speakerVolume"], 0.8)
        cut = next(item for item in track(after, "av")["items"] if item.get("state") == "deleted")
        self.assertEqual((cut["srcStart"], cut["srcEnd"], *span(cut)), (2000, 4000, 2000, 4000))
        self.assertEqual(cut["stateReason"], {"kind": "agent", "by": "lui"})
        self.assertNotIn("state", words(after)[1])
        self.assertEqual(sync.synchronize(index(((0, 2), (4, 2))), after), after)

    def test_noop_preserves_document_bytes_revision_and_mtime(self):
        self.write()
        before = self.path.read_bytes()
        mtime = self.path.stat().st_mtime_ns
        report = sync.sync_workspace(self.root)
        self.assertEqual(report, {"changed": False, "files": [], "av_clips": 1, "caption_words": 2})
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.path.stat().st_mtime_ns, mtime)
        self.assertEqual(sync.validate_workspace(self.root), report)

    def test_atomic_write_and_second_sync_are_idempotent(self):
        self.write(index(((0, 2), (4, 2))))
        with self.assertRaisesRegex(ValueError, "editing_script_out_of_sync"):
            sync.validate_workspace(self.root)
        report = sync.sync_workspace(self.root)
        self.assertTrue(report["changed"])
        self.assertEqual(report["files"], [sync.EDITING_SCRIPT])
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])
        snapshot = self.path.read_bytes()
        self.assertFalse(sync.sync_workspace(self.root)["changed"])
        self.assertEqual(snapshot, self.path.read_bytes())
        self.assertFalse(sync.validate_workspace(self.root)["changed"])

    def test_failed_replace_leaves_original_and_cleans_temporary(self):
        self.write(index(((4, 2),)))
        before = self.path.read_bytes()
        with patch.object(sync.os, "replace", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError):
                sync.sync_workspace(self.root)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob(".editing-script-*.tmp")), [])

    def test_missing_document_is_not_fabricated(self):
        (self.root / "index.html").write_text(index())
        with self.assertRaisesRegex(ValueError, "editing_script_missing_document"):
            sync.sync_workspace(self.root)
        self.assertFalse(self.path.exists())

    def test_invalid_documents_report_codes_without_content(self):
        malformed = [None, {}, {"schemaVersion": 2}, document(), document(), document()]
        malformed[3]["tracks"] = []
        malformed[4]["tracks"][1]["items"][0]["segments"][0]["words"][0] = "sensitive specimen"
        malformed[5]["tracks"][0]["items"][0]["timelineIn"] = "sensitive specimen"
        for doc in malformed:
            with self.subTest(doc_type=type(doc).__name__):
                with self.assertRaisesRegex(ValueError, r"^editing_script_[a-z_]+$"):
                    sync.synchronize(index(), doc)
        self.write()
        for value in ("{private malformed content", '{"rev": 1, "rev": 2}', '{"rev": NaN}'):
            self.path.write_text(value)
            with self.assertRaisesRegex(ValueError, "^editing_script_unreadable_workspace$"):
                sync.sync_workspace(self.root)

    def test_symlink_escape_is_refused(self):
        self.write()
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "editing-script.json"
            target.write_text(self.path.read_text())
            self.path.unlink()
            self.path.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "editing_script_path_outside_workspace"):
                sync.sync_workspace(self.root)

    def test_oversize_file_is_refused(self):
        self.write()
        with patch.object(sync, "MAX_WORKSPACE_TEXT_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "editing_script_unreadable_workspace"):
                sync.sync_workspace(self.root)

    def test_other_tracks_word_style_and_authored_states_are_preserved(self):
        before = document([word("visible", 4000, 4300, emphasis=True, style={"color": "#ff0000"}),
                           word("hidden", 4500, 4700, hidden=True, state="hidden",
                                stateReason={"kind": "user", "by": "gui"}),
                           word("deleted", 5000, 5200, state="deleted",
                                stateReason={"kind": "user", "by": "lui"})])
        extras = [
            {"id": "t-visual-effects", "type": "visualEffects", "items": [{"id": "effect-0", "content": "test"}]},
            {"id": "t-sfx", "type": "sfx", "items": [], "volume": 0.2},
        ]
        before["tracks"].extend(deepcopy(extras))
        track(before, "av")["muted"] = True
        part = track(before, "captions")["items"][0]["segments"][0]
        part["style"], part["position"] = {"fontWeight": "600"}, {"dx": 1, "dy": 2}
        after = sync.synchronize(index(((4, 2),)), before)
        self.assertEqual(after["source"], before["source"])
        self.assertEqual(after["tracks"][2:], extras)
        self.assertTrue(track(after, "av")["muted"])
        for original, updated in zip(words(before), words(after)):
            self.assertEqual({k: v for k, v in original.items() if k not in ("timelineIn", "timelineOut")},
                             {k: v for k, v in updated.items() if k not in ("timelineIn", "timelineOut")})
        updated_part = track(after, "captions")["items"][0]["segments"][0]
        self.assertEqual(updated_part["id"], part["id"])
        self.assertEqual(updated_part["style"], part["style"])
        self.assertEqual(updated_part["position"], part["position"])

    def test_trimmed_word_boundary_rules(self):
        before = document([word("leading", 500, 1200), word("inside", 1500, 2000),
                           word("trailing", 2700, 3200), word("removed", 3300, 4000)])
        after = sync.synchronize(index(((1, 2),)), before)
        self.assertEqual([span(item) for item in words(after)],
                         [(0, 0), (500, 1000), (1700, 2000), (2000, 2000)])

    def test_word_intersecting_two_surviving_intervals_is_refused(self):
        before = document([word("crosses-cut", 1500, 4500)])
        with self.assertRaisesRegex(ValueError, "editing_script_word_spans_cut"):
            sync.synchronize(index(((0, 2), (4, 2))), before)

    def test_authored_words_keep_offsets_when_source_anchor_survives(self):
        inserted = word("authored", None, None)
        inserted.update(timelineIn=4500, timelineOut=4700, origin={"kind": "manual"})
        before = document([word("anchor", 4000, 4400), inserted])
        after = sync.synchronize(index(((4, 2),)), before)
        self.assertEqual([span(item) for item in words(after)], [(0, 400), (500, 700)])
        self.assertEqual(sync.synchronize(index(((4, 2),)), after), after)

    def test_empty_captions_and_missing_av_are_supported(self):
        before = document([])
        before["tracks"] = [{"id": "t-captions", "type": "captions", "items": []}]
        after = sync.synchronize(index(), before)
        self.assertEqual(track(after, "captions"), before["tracks"][0])
        self.assertEqual(track(after, "av")["items"][0]["id"], "clip-0")
        self.assertEqual(sync.synchronize(index(), after), after)

    def test_source_omitted_caption_wrapper_gains_av_without_fabricating_source(self):
        before = document([word("later", 21000, 21500)])
        before.pop("source")
        before["tracks"] = [track(before, "captions")]
        html = index(((20, 2),))
        after = sync.synchronize(html, before)
        self.assertNotIn("source", after)
        self.assertEqual([span(item) for item in words(after)], [(1000, 1500)])
        self.assertEqual([(item["srcStart"], item["srcEnd"]) for item in sync._playing(track(after, "av"))],
                         [(20000, 22000)])
        self.assertEqual(sync.synchronize(html, after), after)

    def test_source_omitted_aligned_av_is_a_noop(self):
        before = document()
        before.pop("source")
        self.assertEqual(sync.synchronize(index(), before), before)
        self.assertEqual(sync.synchronize(index(audio="public/source.enhanced.mp3"), before), before)
        self.write(index(), before)
        self.assertFalse(sync.validate_workspace(self.root)["changed"])
        self.assertFalse(sync.sync_workspace(self.root)["changed"])
        self.assertNotIn("source", json.loads(self.path.read_text()))

    def test_source_omitted_does_not_allow_noncanonical_media_or_anchors(self):
        before = document()
        before.pop("source")
        for html in (index(source="public/other.mp4"), index(audio="out/audio/mix.m4a")):
            with self.subTest(kind="media"):
                with self.assertRaisesRegex(ValueError, "editing_script_unsupported_source"):
                    sync.synchronize(html, before)
        for kind in ("av", "word"):
            current = deepcopy(before)
            item = track(current, "av")["items"][0] if kind == "av" else words(current)[0]
            item["sourceUri"] = "public/other.mp4"
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError, "editing_script_unsupported_source"):
                    sync.synchronize(index(), current)

    def test_explicit_source_metadata_keeps_duration_bound_and_must_be_valid(self):
        with self.assertRaisesRegex(ValueError, "editing_script_source_out_of_bounds"):
            sync.synchronize(index(((20, 2),)), document())
        for invalid in (None, {}, {"path": "public/source.mp4", "duration": None}):
            before = document()
            before["source"] = invalid
            with self.subTest(source_type=type(invalid).__name__):
                with self.assertRaisesRegex(ValueError, "editing_script_unsupported_source"):
                    sync.synchronize(index(), before)

    def test_restore_drops_only_history_now_playing(self):
        before = sync.synchronize(index(((0, 2), (4, 2))), document())
        after = sync.synchronize(index(), before)
        self.assertEqual(len(track(after, "av")["items"]), 1)
        self.assertEqual([span(item) for item in words(after)], [(1000, 1500), (4000, 4500)])

    def test_prior_removal_reason_and_unchanged_clip_metadata_survive(self):
        before = sync.synchronize(index(((0, 2), (4, 2))), document())
        av = track(before, "av")
        av["items"][0]["origin"] = {"kind": "import"}
        removed = next(item for item in av["items"] if item.get("state") == "deleted")
        removed["stateReason"] = {"kind": "pause", "by": "roughcut", "note": "synthetic pause"}
        after = sync.synchronize(index(((0, 2), (4, 1))), before)
        self.assertEqual(track(after, "av")["items"][0]["origin"], {"kind": "import"})
        carried = next(item for item in track(after, "av")["items"] if item["id"] == removed["id"])
        self.assertEqual(carried["stateReason"], removed["stateReason"])
        self.assertEqual(sync.synchronize(index(((0, 2), (4, 1))), after), after)

    def test_multiple_caption_segments_tile_the_new_output(self):
        before = document()
        track(before, "captions")["items"] = [
            {"id": "section-0", "kind": "paragraph", "segments": [
                segment("phrase-0", [word("head", 1000, 1500)], 0, 4000),
                segment("phrase-1", [word("tail", 4000, 4500)], 4000, 6000)]}]
        after = sync.synchronize(index(((0, 2), (4, 2))), before)
        parts = track(after, "captions")["items"][0]["segments"]
        self.assertEqual([span(part) for part in parts], [(0, 2000), (2000, 4000)])

    def test_mismatched_av_or_unsupported_timing_is_refused(self):
        good = index(((0, 2), (4, 2)))
        cases = [
            (good.replace('src="public/source.mp3" data-start="2"',
                          'src="public/source.mp3" data-start="2.1"'), "av_lane_mismatch"),
            (good.replace('data-hf-id="clip-1"', 'data-hf-id="clip-0"'), "duplicate_clip_id"),
            (good.replace('data-start="2"', 'data-start="3"'), "noncontiguous_output"),
            (index(((4, 2), (0, 2))), "unsupported_source_order"),
            (index(((0, 4), (3, 2))), "unsupported_source_order"),
            (index(((0, 7),)), "source_out_of_bounds"),
            (good.replace('data-duration="4"', 'data-duration="6"', 1), "duration_mismatch"),
            (good.replace('data-duration="2"', 'data-duration="NaN"', 1), "invalid_timing"),
            (good.replace('<video ', '<video data-speed="2" ', 1), "unsupported_speed"),
        ]
        for html, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(ValueError, "editing_script_" + code):
                    sync.synchronize(html, document())

    def test_source_clock_must_be_raw_and_single_source(self):
        for html in [index(source="public/recut.mp4"), index(audio="out/audio/mix.m4a"),
                     index(audio="https://example.test/audio.mp3"), index(source="../source.mp4")]:
            with self.subTest(source=html[:45]):
                with self.assertRaisesRegex(ValueError, "editing_script_unsupported_source"):
                    sync.synchronize(html, document())
        self.assertEqual(sync.synchronize(index(audio="public/source.enhanced.mp3"), document()), document())

    def test_mounted_caption_renderer_blocks_changed_geometry_without_partial_write(self):
        host = ('<div class="visual-host clip" data-composition-id="narrator-captions" '
                'data-composition-src="compositions/narrator_captions.html"></div>')
        self.write(index(((4, 2),), extra=host))
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "editing_script_mounted_captions_require_rebake"):
            sync.sync_workspace(self.root)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(sync.synchronize(index(extra=host), document()), document())

    def test_mounted_caption_legacy_display_windows_are_a_true_noop(self):
        host = ('<div class="visual-host clip" data-composition-id="narrator-captions" '
                'data-composition-src="compositions/narrator_captions.html"></div>')
        before = document()
        track(before, "captions")["items"] = [
            {"id": "section-0", "kind": "paragraph", "segments": [
                segment("phrase-0", [word("head", 1000, 1500)], 1000, 1500),
                segment("phrase-1", [word("tail", 4000, 4500)], 4000, 4500)]}]
        for mounted in ("", host):
            with self.subTest(mounted=bool(mounted)):
                self.write(index(extra=mounted), before)
                original = self.path.read_bytes()
                self.assertFalse(sync.sync_workspace(self.root)["changed"])
                self.assertEqual(self.path.read_bytes(), original)
                self.assertEqual(sync.synchronize(index(extra=mounted), before), before)
                self.assertFalse(sync.validate_workspace(self.root)["changed"])

    def test_mounted_adjacent_speaker_split_keeps_caption_render_inputs(self):
        host = ('<div class="visual-host clip" data-composition-id="narrator-captions" '
                'data-composition-src="compositions/narrator_captions.html"></div>')
        before = document([word("crossing", 1500, 2500), word("tail", 4000, 4500)])
        part = track(before, "captions")["items"][0]["segments"][0]
        part.update(timelineIn=1500, timelineOut=4500)
        after = sync.synchronize(index(((0, 2), (2, 4)), extra=host), before)
        self.assertEqual(len(sync._playing(track(after, "av"))), 2)
        self.assertEqual(track(after, "captions"), track(before, "captions"))
        self.assertEqual(sync.synchronize(index(((0, 2), (2, 4)), extra=host), after), after)

    def test_mounted_caption_stale_word_times_still_refuse_on_unchanged_cut(self):
        host = ('<div class="visual-host clip" data-composition-id="narrator-captions" '
                'data-composition-src="compositions/narrator_captions.html"></div>')
        before = document()
        words(before)[0].update(timelineIn=1200, timelineOut=1700)
        with self.assertRaisesRegex(ValueError, "editing_script_mounted_captions_require_rebake"):
            sync.synchronize(index(extra=host), before)

    def test_unused_narrator_file_does_not_block_no_caption_edit(self):
        self.write(index(((4, 2),)))
        (self.path.parent / "narrator_captions.html").write_text("unmounted")
        self.assertTrue(sync.sync_workspace(self.root)["changed"])

    def test_fractional_frames_validate_raw_boundaries_then_tile_rounded_durations(self):
        html = index(((0, 1 / 3), (1 / 3, 1 / 3), (2 / 3, 1 / 3)))
        before = document([word("across-split", 200, 500), word("last", 750, 900)])
        after = sync.synchronize(html, before)
        playing = sync._playing(track(after, "av"))
        self.assertEqual([span(item) for item in playing], [(0, 333), (333, 666), (666, 999)])
        self.assertEqual([span(item) for item in words(after)], [(200, 500), (750, 900)])
        self.assertEqual(sync.synchronize(html, after), after)

    def test_split_without_source_removal_does_not_drop_a_crossing_word(self):
        before = document([word("across-split", 1500, 2500)])
        after = sync.synchronize(index(((0, 2), (2, 4))), before)
        self.assertEqual([span(item) for item in words(after)], [(1500, 2500)])
        self.assertEqual(len(track(after, "av")["items"]), 2)

    def test_decimal_milliseconds_round_half_up_without_float_drift(self):
        self.assertEqual(sync._milliseconds("1.0005"), 1001)
        self.assertEqual(sync._milliseconds("14.649999999999999"), 14650)


if __name__ == "__main__":
    unittest.main()

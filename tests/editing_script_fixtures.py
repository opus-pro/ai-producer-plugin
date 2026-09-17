"""Synthetic preparation output shared by publication tests."""

import json


def write_editing_script(root, duration=59.85):
    path = root / "compositions/editing-script.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    milliseconds = round(duration * 1000)
    path.write_text(json.dumps({
        "schemaVersion": 1, "rev": 0,
        "source": {"path": "public/source.mp4", "duration": milliseconds},
        "tracks": [
            {"id": "t-av", "type": "av", "speakerVolume": 1, "items": [{
                "id": "clip-0", "srcStart": 0, "srcEnd": milliseconds,
                "timelineIn": 0, "timelineOut": milliseconds,
            }]},
            {"id": "t-captions", "type": "captions", "items": []},
        ],
    }), encoding="utf-8")
    return path

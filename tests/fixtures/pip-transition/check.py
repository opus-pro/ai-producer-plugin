"""Verify editable PIP ownership in a standalone synthetic browser fixture."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1]).resolve()
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 360, "height": 640}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto((root / "index.html").as_uri())
    page.wait_for_function("window.seekGlobal && document.querySelector('#speaker').readyState >= 2")
    assert page.locator("video").count() == 2
    assert page.locator("#effect-speaker").get_attribute("src") is None
    assert page.locator("#effect-speaker").get_attribute("data-pip-src") == "public/synthetic.webm"

    def styles(selector, keys):
        return page.evaluate(
            """([selector, keys]) => {
              const s = getComputedStyle(document.querySelector(selector));
              return Object.fromEntries(keys.map(k => [k, s[k]]));
            }""",
            [selector, keys],
        )

    root_keys = ["left", "top", "width", "height", "borderRadius", "objectPosition"]
    frame_keys = ["left", "top", "width", "height", "borderRadius"]
    expected_root = {
        "left": "0px", "top": "0px", "width": "360px", "height": "640px",
        "borderRadius": "0px", "objectPosition": "50% 50%",
    }

    def sample(time):
        page.evaluate("time => window.seekGlobal(time)", time)
        return {
            "root": styles("#speaker", root_keys),
            "frame": styles(".speaker-pip-frame", frame_keys),
            "host_display": styles("#pip-host", ["display"])["display"],
        }

    times = [1, 1.15, 1.3, 1.45, 1.6, 3, 4.4, 4.55, 4.7, 4.85, 4.999]
    forward = {str(t): sample(t) for t in times}
    backward = {str(t): sample(t) for t in reversed(times)}
    assert forward == backward, (forward, backward)
    assert all(value["root"] == expected_root for value in forward.values())
    for key in ("left", "top", "width", "height", "borderRadius"):
        assert abs(float(forward["1"]["frame"][key][:-2]) - float(forward["4.999"]["frame"][key][:-2])) < 0.1
    mid = forward["1.3"]["frame"]
    assert 0 < float(mid["left"][:-2]) < 24
    assert 0 < float(mid["top"][:-2]) < 340
    assert 312 < float(mid["width"][:-2]) < 360
    assert 276 < float(mid["height"][:-2]) < 640
    assert 0 < float(mid["borderRadius"][:-2]) < 30

    page.evaluate("window.moveHost(1.5)")
    page.evaluate("window.seekGlobal(1.2)")
    assert styles("#pip-host", ["display"])["display"] == "none"
    assert styles("#speaker", root_keys) == expected_root
    page.evaluate("window.seekGlobal(2.1)")
    assert styles("#pip-host", ["display"])["display"] == "block"
    assert styles("#speaker", root_keys) == expected_root

    for label, time in [("full", 1), ("enter-mid", 1.3), ("pip", 3), ("exit-mid", 4.7)]:
        page.evaluate("window.moveHost(1)")
        page.evaluate("time => window.seekGlobal(time)", time)
        page.screenshot(path=str(root / (label + ".png")))

    page.evaluate("window.deleteHost(); window.seekGlobal(3)")
    assert page.locator("#pip-host").count() == 0
    assert styles("#speaker", root_keys) == expected_root
    assert not errors, errors
    (root / "geometry.json").write_text(json.dumps({
        "scope": "standalone effect ownership; not AIP editor or export",
        "forward": forward,
        "backward_equal": True,
        "root_unchanged": True,
        "move_old_time_clear": True,
        "delete_residual_clear": True,
        "errors": errors,
    }, indent=2))
    browser.close()
print("PASS: deterministic PIP geometry, root unchanged, move/delete leave no residual geometry")

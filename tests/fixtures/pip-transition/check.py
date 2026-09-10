"""Verify synthetic geometry, not AIP integration. Requires Playwright Chromium.

Run against an absolute staging directory holding index.html, a locally supplied
public/vendor/gsap.min.js and a generated public/synthetic.webm. No user media.
"""
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
    page.wait_for_function("window.__timelines && document.querySelector('video').readyState >= 2")
    assert page.locator('video').count() == 1
    def sample(t):
        return page.evaluate("""t => {
          window.__timelines['finecut-root'].seek(t);
          const s = getComputedStyle(document.querySelector('#speaker'));
          return Object.fromEntries(['left','top','width','height','borderRadius','objectPosition'].map(k => [k,s[k]]));
        }""", t)
    times = [0, 1, 1.15, 1.3, 1.45, 1.6, 3, 4, 4.15, 4.3, 4.45, 4.6, 6]
    forward = {str(t): sample(t) for t in times}
    backward = {str(t): sample(t) for t in reversed(times)}
    assert forward == backward, (forward, backward)
    assert forward['0'] == forward['6']
    mid = forward['1.3']
    assert 0 < float(mid['left'][:-2]) < 24
    assert 0 < float(mid['top'][:-2]) < 340
    assert 312 < float(mid['width'][:-2]) < 360
    assert 276 < float(mid['height'][:-2]) < 640
    assert 0 < float(mid['borderRadius'][:-2]) < 30
    assert mid['objectPosition'] not in ('50% 50%', '50% 28%')
    # Nearby samples across transition endpoints must not jump to another frame.
    for boundary in (1, 1.6, 4, 4.6):
        a, b = sample(boundary - .001), sample(boundary + .001)
        for key in ('left', 'top', 'width', 'height', 'borderRadius'):
            assert abs(float(a[key][:-2]) - float(b[key][:-2])) < 1
    for label, time in [('full', 0), ('enter-mid', 1.3), ('pip', 3), ('exit-mid', 4.3), ('return', 6)]:
        sample(time)
        page.screenshot(path=str(root / (label + '.png')))
    assert not errors, errors
    (root / 'geometry.json').write_text(json.dumps({'scope':'standalone synthetic DOM/GSAP; not AIP editor or export', 'forward':forward, 'backward_equal': True, 'decoder_elements':1, 'errors':errors}, indent=2))
    browser.close()
print('PASS: 13 forward/backward poses, 4 boundary continuity checks, single video, no JS errors')

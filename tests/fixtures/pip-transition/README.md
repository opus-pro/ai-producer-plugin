# PIP geometry fixture

This six-second synthetic fixture checks a single root video moving between full-screen and rounded lower PIP. It is not an uploadable AIP project: the material card stays inline to isolate the geometry, and there is no speaker audio. It does not test editor track movement, camera edits, cut clips, audio synchronization or export.

Stage `index.html` in an ignored scratch directory. Supply a local GSAP build at `public/vendor/gsap.min.js`; third-party code is not vendored by this fixture. Generate synthetic media in that staging directory:

```sh
ffmpeg -v error -f lavfi -i 'testsrc2=size=360x640:rate=10' -t 6 -c:v libvpx-vp9 public/synthetic.webm
python /absolute/path/to/check.py /absolute/path/to/staging-directory
```

The check requires Python Playwright and installed Google Chrome. It checks thirteen forward/backward geometry poses, four transition boundaries, a single video element and JavaScript errors. Screenshots and `geometry.json` are written only to the supplied staging directory. It keeps the synthetic video on its decoded first frame while seeking geometry; it does not assert video-frame synchronization. Production composition timing and media playback remain owned by AIP.

# Editable PIP ownership fixture

This six-second synthetic fixture checks an effect-owned speaker PIP. The root speaker remains full frame while a visual host owns an opaque ground, a muted `data-pip-src` view and the full-frame/PIP geometry timeline. It is not an uploadable AIP project: the child template is embedded so the standalone browser check can mount it without an editor.

Stage `index.html` in an ignored scratch directory. Supply a local GSAP build at `public/vendor/gsap.min.js`; third-party code is not vendored by this fixture. Generate synthetic root media in that staging directory:

```sh
ffmpeg -v error -f lavfi -i 'testsrc2=size=360x640:rate=10' -t 6 -c:v libvpx-vp9 public/synthetic.webm
python /absolute/path/to/check.py /absolute/path/to/staging-directory
```

The check requires Python Playwright and installed Google Chrome. It checks deterministic forward/backward PIP geometry, an unchanged root speaker, a host move with no effect at the old time, and host deletion with no residual geometry. Screenshots and `geometry.json` are written only to the supplied staging directory. The nested `data-pip-src` view deliberately has no `src`; production media playback and cut mapping remain owned by AIP.

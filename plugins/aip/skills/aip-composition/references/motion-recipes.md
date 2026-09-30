# Motion recipes

Worked motion definitions for the [composition contract](../SKILL.md)'s motion host. Copy one into a single `<script data-aip-motion="<name>">` in `index.html`, keep its name, and place one host per use. Adapt freely: the contract is the host, the channels and their bounds, and a `frame` computed from its arguments alone. The preflight samples every definition when Node is available.

A host that uses one of them:

```html
<div
  class="visual-host clip"
  data-composition-id="hit-1"
  data-aip-effect="motion"
  data-no-timeline
  data-start="41.2"
  data-duration="0.4"
  data-src-anchor="53.3"
  data-track-index="900"
  data-hide-captions="false"
  data-effect-motion="impact-shake"
  data-effect-params='{"amplitude":18}'
></div>
```

Two treatments on one beat (a shake and a flash on the same slam) are two hosts with the same start on two tracks, 900 and 901.

## Impact shake

A slam, a stamp, a number landing. Full strength on the first frame, gone within half a second. Keep it to 0.2 to 0.45 s.

```js
(window.__aipMotions = window.__aipMotions || {})["impact-shake"] = {
  label: "Impact shake",
  params: {
    amplitude: { min: 2, max: 40, default: 16, label: "Shake", unit: "px" },
  },
  frame: function (t, d, p, rand) {
    var e = Math.pow(1 - t / d, 2) * p.amplitude;
    return {
      x: e * Math.sin(97.3 * t + rand(0)),
      y: 0.8 * e * Math.sin(73.1 * t + rand(1)),
      rotate: 0.035 * e * Math.sin(51.7 * t + rand(2)),
    };
  },
};
```

## White flash

A hard section change or the peak of a reveal. It covers the captions for its few frames, so keep it under 0.35 s.

```js
(window.__aipMotions = window.__aipMotions || {})["white-flash"] = {
  label: "Flash",
  params: { strength: { min: 0.1, max: 1, default: 0.9, label: "Strength" } },
  frame: function (t, d, p) {
    return {
      overlay: {
        color: "#ffffff",
        opacity: p.strength * Math.min(1, t / 0.04) * Math.pow(1 - t / d, 2),
      },
    };
  },
};
```

## Whip

A jolt sideways and back, for "but" or a turn in the argument. 0.25 to 0.4 s.

```js
(window.__aipMotions = window.__aipMotions || {})["whip"] = {
  label: "Whip",
  params: {
    distance: {
      min: -160,
      max: 160,
      default: 120,
      label: "Distance",
      unit: "px",
    },
  },
  frame: function (t, d, p) {
    var s = Math.sin((Math.PI * t) / d);
    return { x: p.distance * s * s, scale: 1 + 0.06 * s };
  },
};
```

## Push in

A slow push while the speaker builds to a point, over one or two sentences.

```js
(window.__aipMotions = window.__aipMotions || {})["push-in"] = {
  label: "Push in",
  params: { amount: { min: 0.02, max: 0.4, default: 0.12, label: "Push" } },
  frame: function (t, d, p) {
    return { scale: 1 + p.amount * (1 - Math.pow(1 - t / d, 3)) };
  },
};
```

## Handheld drift

A restless, documentary feel under a confession or an aside. Low amplitude, a few seconds at most.

```js
(window.__aipMotions = window.__aipMotions || {})["handheld"] = {
  label: "Handheld",
  params: {
    amount: { min: 1, max: 12, default: 4, label: "Drift", unit: "px" },
  },
  frame: function (t, d, p, rand) {
    var ramp = Math.max(0, Math.min(1, t / 0.4, (d - t) / 0.4));
    var a = p.amount * ramp;
    return {
      x: a * (Math.sin(1.3 * t + rand(0)) + 0.5 * Math.sin(2.9 * t + rand(1))),
      y: a * (Math.sin(1.7 * t + rand(2)) + 0.5 * Math.sin(3.1 * t + rand(3))),
      rotate: 0.15 * ramp * Math.sin(0.9 * t + rand(4)),
    };
  },
};
```

## Beat pulse

A single bump in scale on a stressed word. 0.2 to 0.3 s.

```js
(window.__aipMotions = window.__aipMotions || {})["beat-pulse"] = {
  label: "Pulse",
  params: { amount: { min: 0.01, max: 0.15, default: 0.05, label: "Pulse" } },
  frame: function (t, d, p) {
    return { scale: 1 + p.amount * Math.sin((Math.PI * t) / d) };
  },
};
```

## Glitch step

A digital stutter: the picture jumps between held offsets at 12 steps a second, then settles. The steps come from `rand`, never from `Math.random`.

```js
(window.__aipMotions = window.__aipMotions || {})["glitch-step"] = {
  label: "Glitch",
  params: {
    amount: { min: 4, max: 60, default: 24, label: "Glitch", unit: "px" },
  },
  frame: function (t, d, p, rand) {
    var step = Math.floor(t * 12);
    var e = p.amount * (1 - t / d);
    return {
      x: e * Math.sin(rand(step)),
      y: 0.3 * e * Math.cos(rand(step + 100)),
    };
  },
};
```

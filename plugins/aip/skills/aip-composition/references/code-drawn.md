# Code-drawn layers: Canvas 2D, WebGL2 and Three.js

<!-- SPDX-License-Identifier: Apache-2.0 -->

Copyright 2026 HeyGen, Inc. Modifications Copyright 2026 OpusClip. Modified by OpusClip for AIP; see [source attribution, license, and changes](../../../THIRD_PARTY_NOTICES.md).

A composition may paint a `<canvas>` from script when a shape, a field or a 3D object explains the beat better than DOM elements can. The canvas is one leaf inside an ordinary composition: the host, the template, the paused timeline and its registration are exactly as in the [composition contract](../SKILL.md). This page covers only what a canvas adds.

## What the service provides

- Canvas 2D and WebGL2 are browser built-ins; write them inline.
- Three.js r160 is provided by the service at `public/vendor/three.min.js`, as the global `THREE` (the UMD build, not an ES module). Load it from a composition as `<script src="../public/vendor/three.min.js"></script>`, beside GSAP. The service writes the file in the commit that first names it, so do not upload it; the local preflight counts it as present. No other library is available, and a script from outside the project is refused.

## The rules the commit enforces

`commit_workspace` judges a document that calls `getContext(` or builds a `WebGLRenderer`:

- `code_drawn_clock` refuses `requestAnimationFrame`, `setAnimationLoop`, `setTimeout` and `setInterval`. The editor and the export move a composition only by seeking its paused timeline, so a frame on another clock keeps moving while the editor is paused and ignores scrubbing. Draw from the timeline instead.
- `webgl_context_not_released` refuses a WebGL context that is never released with `loseContext()` or `forceContextLoss()`. The editor keeps every composition mounted and seeks every timeline on each jump, and the browser keeps at most 16 live WebGL contexts per page, so a context must exist only while its moment is on screen.
- `three_used_before_load` warns when a document loads `three.min.js` and never tests `window.THREE`. The editor runs a composition's inline script before its vendor scripts finish loading, so a top-level `THREE` use throws there, and the moment never plays in the editor while the export plays it.
- `code_drawn_nondeterministic` warns on `Math.random`, `Date` and `performance.now`. A frame that reads one differs between the editor, the export and each export attempt. Use a seeded generator and the timeline's time.

The local [preflight](../../aip/scripts/preflight.py) reports the same codes before upload.

## The shape every kind shares

- Drive the canvas from a proxy tween on the moment's own paused timeline: `{t: 0}` to `{t: duration}` with `ease: "none"` and an `onUpdate` that calls `draw(t)`. Nothing else schedules a frame, and every frame is computed from `t` alone.
- `draw(t)` returns without drawing, and releases any WebGL context, when `t` is at or past either edge of the window. The editor fires `onUpdate` at those edge states for every moment on every seek, so a moment that is not on screen holds no context.
- Create the context on the first draw inside the window, not at load. A released or lost context cannot be recreated on the same element: replace the canvas with `canvas.cloneNode(false)` first.
- Size the canvas to the composition (`width="1080" height="1920"` for a portrait project) and position it absolutely; DOM text such as a label sits over it as ordinary elements.
- Keep data inline and fetch nothing.
- A canvas is one leaf to the editor: the user can move, trim or delete the moment, not edit what it draws.

## Canvas 2D

```html
<template>
  <div data-composition-id="bars" data-width="1080" data-height="1920">
    <style>
      [data-composition-id="bars"] canvas {
        position: absolute;
        left: 0;
        top: 0;
        width: 1080px;
        height: 1920px;
      }
    </style>
    <canvas class="cv" width="1080" height="1920"></canvas>
    <script src="../public/vendor/gsap.min.js"></script>
    <script>
      (function () {
        const root = document.querySelector('[data-composition-id="bars"]');
        const tl = gsap.timeline({ paused: true });
        const DUR = 4;
        const VALUES = [0.42, 0.67, 0.91];
        const ctx = root.querySelector(".cv").getContext("2d");
        function draw(t) {
          const p = Math.min(1, t / 1.2);
          ctx.clearRect(0, 0, 1080, 1920);
          ctx.fillStyle = "#d8643f";
          VALUES.forEach(function (v, i) {
            const h = 900 * v * p;
            ctx.fillRect(180 + i * 260, 1400 - h, 180, h);
          });
        }
        const st = { t: 0 };
        tl.to(
          st,
          {
            t: DUR,
            duration: DUR,
            ease: "none",
            onUpdate: function () {
              draw(st.t);
            },
          },
          0,
        );
        window.__timelines = window.__timelines || {};
        window.__timelines["bars"] = tl;
      })();
    </script>
  </div>
</template>
```

## WebGL2

```html
<script>
  (function () {
    const root = document.querySelector('[data-composition-id="field"]');
    const tl = gsap.timeline({ paused: true });
    const DUR = 4;
    let cv = root.querySelector(".cv");
    let gl = null;
    let uT = null;
    const VS =
      "#version 300 es\nin vec2 p; out vec2 uv; void main() { uv = p * 0.5 + 0.5; gl_Position = vec4(p, 0.0, 1.0); }";
    const FS =
      "#version 300 es\nprecision highp float; in vec2 uv; out vec4 o; uniform float u_t;\n" +
      "void main() { float w = 0.5 + 0.5 * sin(uv.x * 12.0 + u_t * 2.0); o = vec4(mix(vec3(0.16, 0.06, 0.07), vec3(0.85, 0.39, 0.25), w), 1.0); }";
    function init() {
      gl = cv.getContext("webgl2", { preserveDrawingBuffer: true });
      if (!gl) return false;
      function shader(type, src) {
        const s = gl.createShader(type);
        gl.shaderSource(s, src);
        gl.compileShader(s);
        return s;
      }
      const prog = gl.createProgram();
      gl.attachShader(prog, shader(gl.VERTEX_SHADER, VS));
      gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, FS));
      gl.linkProgram(prog);
      gl.useProgram(prog);
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
      gl.bufferData(
        gl.ARRAY_BUFFER,
        new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
        gl.STATIC_DRAW,
      );
      const loc = gl.getAttribLocation(prog, "p");
      gl.enableVertexAttribArray(loc);
      gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      uT = gl.getUniformLocation(prog, "u_t");
      return true;
    }
    function fresh() {
      const next = cv.cloneNode(false);
      cv.replaceWith(next);
      cv = next;
      gl = null;
    }
    function release() {
      if (!gl) return;
      const ext = gl.getExtension("WEBGL_lose_context");
      if (ext) ext.loseContext();
      fresh();
    }
    function onScreen(t) {
      if (t > 0.0001 && t < DUR - 0.0001) return true;
      // Local 0 is both "before the window" and its first frame, where a click on the
      // moment lands; only the root clock tells them apart.
      const host = root.closest(".visual-host");
      const rootTl = window.__timelines && window.__timelines["finecut-root"];
      if (t > 0.0001 || !host || !rootTl) return false;
      return rootTl.time() >= parseFloat(host.getAttribute("data-start")) - 0.01;
    }
    function draw(t) {
      if (!onScreen(t)) {
        release();
        return;
      }
      if (gl && gl.isContextLost()) fresh();
      if (!gl && !init()) return;
      gl.viewport(0, 0, 1080, 1920);
      gl.uniform1f(uT, t);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
    const st = { t: 0 };
    tl.to(
      st,
      {
        t: DUR,
        duration: DUR,
        ease: "none",
        onUpdate: function () {
          draw(st.t);
        },
      },
      0,
    );
    window.__timelines = window.__timelines || {};
    window.__timelines["field"] = tl;
  })();
</script>
```

The template, style and canvas are as in the Canvas 2D example. Name GLSL identifiers plainly: a GLSL ES reserved word such as `input`, `output`, `filter` or `sample` as a variable name fails to compile and draws nothing.

## Three.js

```html
<script src="../public/vendor/three.min.js"></script>
<script src="../public/vendor/gsap.min.js"></script>
<script>
  (function () {
    const root = document.querySelector('[data-composition-id="orb"]');
    const tl = gsap.timeline({ paused: true });
    const DUR = 5;
    let cv = root.querySelector(".cv");
    let R = null;
    let scene = null;
    let cam = null;
    let mesh = null;
    let lastT = 0;
    function init() {
      if (!window.THREE) return false;
      const T = window.THREE;
      R = new T.WebGLRenderer({
        canvas: cv,
        alpha: true,
        antialias: true,
        preserveDrawingBuffer: true,
      });
      R.setPixelRatio(1);
      R.setSize(1080, 1920, false);
      scene = new T.Scene();
      cam = new T.PerspectiveCamera(32, 1080 / 1920, 0.1, 100);
      cam.position.set(0, 0, 13);
      mesh = new T.Mesh(
        new T.IcosahedronGeometry(1.6, 4),
        new T.MeshStandardMaterial({ color: 0xd8643f, roughness: 0.5 }),
      );
      scene.add(mesh);
      scene.add(new T.HemisphereLight(0xf1eedd, 0x2a1012, 1.6));
      return true;
    }
    function release() {
      if (!R) return;
      R.forceContextLoss();
      R.dispose();
      mesh.geometry.dispose();
      mesh.material.dispose();
      const next = cv.cloneNode(false);
      cv.replaceWith(next);
      cv = next;
      R = null;
    }
    function onScreen(t) {
      if (t > 0.0001 && t < DUR - 0.0001) return true;
      // Local 0 is both "before the window" and its first frame, where a click on the
      // moment lands; only the root clock tells them apart.
      const host = root.closest(".visual-host");
      const rootTl = window.__timelines && window.__timelines["finecut-root"];
      if (t > 0.0001 || !host || !rootTl) return false;
      return rootTl.time() >= parseFloat(host.getAttribute("data-start")) - 0.01;
    }
    function draw(t) {
      lastT = t;
      if (!onScreen(t)) {
        release();
        return;
      }
      if (R && R.getContext().isContextLost()) release();
      if (!R && !init()) return;
      mesh.rotation.y = t * 0.6;
      R.render(scene, cam);
    }
    const tag =
      root.querySelector('script[src$="three.min.js"]') ||
      document.querySelector('script[src$="three.min.js"]');
    if (tag && !window.THREE)
      tag.addEventListener("load", function () {
        draw(lastT);
      });
    const st = { t: 0 };
    tl.to(
      st,
      {
        t: DUR,
        duration: DUR,
        ease: "none",
        onUpdate: function () {
          draw(st.t);
        },
      },
      0,
    );
    window.__timelines = window.__timelines || {};
    window.__timelines["orb"] = tl;
  })();
</script>
```

`init()` reads `window.THREE` on the first draw and returns false until the file has loaded; the `load` listener then redraws the time the editor last asked for. Everything Three.js creates is released with the context, so a moment that is seeked away from and back again rebuilds its scene. Keep geometry detail modest: the whole scene is rebuilt on each entry.

## First frame

`onScreen(t)` is how a WebGL skeleton decides whether to hold a context. Inside the window the local time decides alone. At local `t = 0` it cannot: the editor seeks a moment to 0 both while the playhead is before the window and when the playhead sits on the window's first frame, which is where clicking the moment on the timeline lands. So at 0 the skeleton compares the root timeline's time with the host's live `data-start`, read at draw time because the user can move the host. The editor seeks the root timeline before the compositions, so the root time is current there; where it is not, the first frame is skipped and nothing else changes. `root.closest(".visual-host")` finds the host in both the editor and the export mount, whichever element carries the composition id there.

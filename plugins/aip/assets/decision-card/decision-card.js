/*
 * AI Producer decision card, packaged for hosts that render agent-authored HTML widgets.
 * Generated from the AI Producer service's decision card resource ui://aip/decision-card/v29.
 * Do not edit by hand: regenerate it from the service.
 *
 * Load it with a <script src> pinned to a release, then call
 * AIPDecisionCard.render(structuredContent, { mount: "<element id>", key: "<unique id>" })
 * with the present_choices result. A selection is sent through the host's sendPrompt; the
 * key keeps the sent state when the widget remounts.
 */
(function () {
  "use strict";
  var current = document.currentScript || document.querySelector('script[src$="/decision-card.js"]');
  var BASE = current && current.src ? current.src.replace(/[^/]*$/, "") : "";
  var TILE_PATH = /[/]caption-card-tiles[/]v1[/]([a-z0-9-]+[.]mp4)$/;
  var STYLE = "\n:root {\n  color-scheme: light dark;\n  /* The card's palette, per the decision card design (Figma 2695-745952). The design is\n     drawn dark - white text, white at 5% and 10% for surfaces, a white primary button with\n     black text - and the light scheme mirrors it in black, so a selection is always drawn\n     in the text colour rather than a hue the host's theme never chose. Secondary text is\n     60% black on light rather than the mirrored 50%, which falls under 4.5:1 on a surface. */\n  --fg: light-dark(#000, #fff);\n  --fg-2: light-dark(rgba(0,0,0,.6), rgba(255,255,255,.5));\n  --surface: light-dark(rgba(0,0,0,.05), rgba(255,255,255,.05));\n  --tonal: light-dark(rgba(0,0,0,.1), rgba(255,255,255,.1));\n  --accent: var(--fg);\n  --on-accent: light-dark(#fff, #000);\n  --line: rgba(128,128,128,.35);\n  /* The app's --ease-out-quart (apps/web/app/globals.css), for 150-300ms UI motion. */\n  --ease-out: cubic-bezier(0.25, 1, 0.5, 1);\n  /* How long a gate's fold takes; the visibility flip waits exactly this long. */\n  --fold-time: .2s;\n}\n* { box-sizing: border-box; }\nbody { margin: 0; padding: 16px; font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, sans-serif; }\n#card-shell#card-shell h1 { font-size: 18px; line-height: 21.8px; font-weight: 600; margin: 0 0 4px; }\n#card-shell#card-shell h2 { font-size: 14px; margin: 0 0 2px; }\n#card-shell#card-shell .note, #card-shell#card-shell .sub { opacity: .75; margin: 0 0 12px; }\n#card-shell#card-shell .group { border: 1px solid var(--line); border-radius: 10px; padding: 12px; margin-bottom: 12px; }\n#card-shell#card-shell .warn { border-left: 3px solid #d08700; padding-left: 8px; margin: 6px 0 10px; font-size: 13px; opacity: .9; }\n#card-shell#card-shell .opts { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin-top: 10px; }\n#card-shell#card-shell .opt { display: flex; flex-direction: column; border: 1px solid rgba(128,128,128,.35); border-radius: 8px; }\n/* A column, so the opener can be pushed to the bottom: in flow it followed a description\n   of whatever length and landed at a different height on every tile of the row. */\n#card-shell#card-shell .opt label { display: flex; flex-direction: column; flex: 1 1 auto; padding: 8px; cursor: pointer; }\n#card-shell#card-shell .opt[data-on=\"1\"] { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }\n#card-shell#card-shell .opt input { margin-right: 6px; accent-color: var(--accent); }\n#card-shell#card-shell .opt img, #card-shell#card-shell .opt video { display: block; width: 100%; border-radius: 6px; margin-bottom: 6px; background: rgba(128,128,128,.15); }\n#card-shell#card-shell .opt > video { width: auto; margin: 8px 8px 0; } /* Outside the label: insets itself, and that frame does not select. */\n#card-shell#card-shell .opt .name { font-weight: 600; }\n#card-shell#card-shell .opt .why { font-size: 12px; opacity: .75; margin: 4px 0; max-height: 4.5em; overflow: hidden; }\n#card-shell#card-shell .opt .why[data-open=\"1\"] { max-height: none; }\n#card-shell#card-shell .opt .more { font-size: 11px; padding: 1px 6px; margin-top: auto; align-self: flex-start; border-radius: 6px; }\n#card-shell#card-shell .tag { font-size: 11px; border: 1px solid rgba(128,128,128,.5); border-radius: 99px; padding: 0 6px; margin-left: 4px; }\n/* One typed question, one row: the label sits beside its field rather than above it. */\n#card-shell#card-shell .field { display: flex; gap: 8px; align-items: center; margin: 0 0 6px; }\n#card-shell#card-shell .field .rowlabel { flex: 0 0 34%; max-width: 180px; font-size: 13px; opacity: .85; overflow-wrap: break-word; }\n#card-shell#card-shell .field input[type=\"text\"] { flex: 1 1 auto; min-width: 0; font: inherit; padding: 6px 8px; border-radius: 8px; border: 1px solid rgba(128,128,128,.5); background: transparent; color: inherit; }\n#card-shell#card-shell .field input[type=\"color\"] { flex: 0 0 auto; width: 40px; height: 32px; padding: 0; border: 1px solid rgba(128,128,128,.5); border-radius: 8px; background: transparent; }\n#card-shell#card-shell .field input[data-bad=\"1\"], #card-shell#card-shell .field textarea[data-bad=\"1\"] { border-color: #d08700; }\n/* A field revealed by one option of the picker above it: no side label, and the full width\n   of the group it was drawn into. */\n#card-shell#card-shell .reveal { margin-top: 10px; }\n#card-shell#card-shell .reveal .hint { margin: 6px 0 0; }\n#card-shell#card-shell .field.bare { display: block; margin: 0; }\n#card-shell#card-shell .field textarea { display: block; width: 100%; font: inherit; padding: 6px 8px; border-radius: 8px; border: 1px solid rgba(128,128,128,.5); background: transparent; color: inherit; resize: vertical; }\n/* One sentence for every typed question on the card, at its foot. */\n#card-shell#card-shell .hint { font-size: 12px; opacity: .75; margin: 8px 0 12px; }\n/* A question drawn as a row: pictogram, label with its line, control at the right edge. */\n#card-shell#card-shell .rowgroup { padding: 12px 14px; }\n#card-shell#card-shell .row { display: flex; align-items: center; gap: 12px; cursor: pointer; }\n#card-shell#card-shell .row .ico { flex: 0 0 auto; width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; opacity: .9; }\n#card-shell#card-shell .rowtext { flex: 1 1 auto; min-width: 0; }\n#card-shell#card-shell .rowlabel { font-weight: 600; }\n#card-shell#card-shell .rowdesc { font-size: 12px; opacity: .7; }\n#card-shell#card-shell .rowdesc:empty { display: none; }\n/* The input is the control; the knob is what a person sees of it. */\n#card-shell#card-shell .switch { position: relative; flex: 0 0 auto; width: 40px; height: 22px; cursor: pointer; }\n#card-shell#card-shell .switch input { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0; cursor: pointer; }\n#card-shell#card-shell .switch .knob { position: absolute; inset: 0; border-radius: 99px; background: rgba(128,128,128,.45); transition: background .15s; }\n#card-shell#card-shell .switch .knob::after { content: \"\"; position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: transform .15s; }\n#card-shell#card-shell .switch input:checked + .knob { background: var(--accent); }\n#card-shell#card-shell .switch input:checked + .knob::after { background: var(--on-accent); }\n#card-shell#card-shell .switch input:checked + .knob::after { transform: translateX(18px); }\n#card-shell#card-shell .switch input:focus-visible + .knob { outline: 2px solid var(--accent); outline-offset: 2px; }\n#card-shell#card-shell .switch input[disabled] + .knob { opacity: .6; }\n#card-shell#card-shell .gategroup .opts { margin-top: 12px; }\n/* A gate's hint and tiles fold under its row: the one track eases between 0fr and 1fr with\n   the fade, so the card's height (and the frame the host sizes from it) moves over 200ms\n   instead of jumping. Visibility flips after the fold has closed and at once when it opens,\n   so folded tiles stay out of reach even where inert is unsupported. The inner box clips,\n   which also holds its children's margins inside the track. */\n#card-shell#card-shell .fold { display: grid; grid-template-rows: 1fr; opacity: 1; transition: grid-template-rows var(--fold-time) var(--ease-out), opacity var(--fold-time) var(--ease-out), visibility 0s; }\n#card-shell#card-shell .fold[data-open=\"0\"] { grid-template-rows: 0fr; opacity: 0; visibility: hidden; transition: grid-template-rows var(--fold-time) var(--ease-out), opacity var(--fold-time) var(--ease-out), visibility 0s var(--fold-time); }\n#card-shell#card-shell .foldin { min-height: 0; overflow: hidden; }\n/* The gate's line eases to its new height over the same time and curve when its copy changes\n   with the switch, so its wrap cannot push the card against the fold. */\n#card-shell#card-shell .gategroup .rowdesc { transition: height var(--fold-time) var(--ease-out); }\n#card-shell#card-shell .gategroup .rowdesc[data-easing=\"1\"] { overflow: hidden; }\n@media (prefers-reduced-motion: reduce) { #card-shell#card-shell .fold, #card-shell#card-shell .fold[data-open=\"0\"], #card-shell#card-shell .gategroup .rowdesc { transition: none; } }\n/* Radio rows, each its own box; a picked row may open a segmented control and the line\n   saying what its current segment does. Sizes are the design's: 12px boxes 8px apart, a 16px\n   radio drawn as a ring that fills when picked, 32px segments in a 10px track. */\n#card-shell#card-shell .rowsgroup { border: none; padding: 0; }\n#card-shell#card-shell .rowbox { border-radius: 12px; padding: 12px; margin-bottom: 8px; background: var(--surface); }\n#card-shell#card-shell .rowbox .row { gap: 8px; }\n#card-shell#card-shell .rowbox .rowtext { padding: 0 2px; }\n#card-shell#card-shell .rowbox .rowlabel { font-weight: 500; line-height: 17px; }\n#card-shell#card-shell .rowbox .rowdesc { color: var(--fg-2); opacity: 1; line-height: 19px; }\n#card-shell#card-shell .rowbox .row .ico { width: 24px; height: 24px; opacity: 1; }\n#card-shell#card-shell .ico.solid { fill: currentColor; fill-rule: evenodd; stroke: none; }\n#card-shell#card-shell .rowbox .row input[type=\"radio\"] { appearance: none; flex: 0 0 auto; width: 16px; height: 16px; margin: 0; border-radius: 50%; border: 1px solid var(--fg-2); background: transparent; cursor: pointer; }\n#card-shell#card-shell .rowbox .row input[type=\"radio\"]:checked { border: 2px solid var(--fg); background: radial-gradient(circle, var(--fg) 0 3px, var(--on-accent) 3.5px); }\n#card-shell#card-shell .rowbox .row input[type=\"radio\"]:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }\n#card-shell#card-shell .rowbox .row input[type=\"radio\"][disabled] { opacity: .6; cursor: default; }\n#card-shell#card-shell .segments { display: flex; height: 32px; margin-top: 16px; border-radius: 10px; overflow: hidden; background: var(--surface); }\n#card-shell#card-shell .seg { flex: 1 1 0; min-width: 0; height: 32px; padding: 0 8px; border: none; border-radius: 8px; background: transparent; color: var(--fg-2); font-weight: 500; line-height: 17px; }\n#card-shell#card-shell .seg[data-on=\"1\"] { background: var(--tonal); color: var(--fg); }\n#card-shell#card-shell .seg:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }\n#card-shell#card-shell .segdesc { margin-top: 6px; }\n/* A rows picker's segments and their line fold open and shut: the row track runs 0fr to 1fr\n   while the content fades, 200ms on the product's ease-out-quart, so the card grows over the\n   same frames the host reads its size on. Reduced motion lands on the end state at once. */\n#card-shell#card-shell .segfold { display: grid; grid-template-rows: 1fr; opacity: 1; transition: grid-template-rows 200ms cubic-bezier(0.25, 1, 0.5, 1), opacity 200ms cubic-bezier(0.25, 1, 0.5, 1); }\n#card-shell#card-shell .segfold[data-open=\"0\"] { grid-template-rows: 0fr; opacity: 0; }\n#card-shell#card-shell .segfoldin { min-height: 0; overflow: hidden; }\n@media (prefers-reduced-motion: reduce) { #card-shell#card-shell .segfold { transition: none; } }\n#card-shell#card-shell .gategroup .warn { margin-top: 10px; }\n/* The typed field with shortcut chips under it, per the Fine cut design (Figma 2695-934065):\n   no box around the section, a secondary label, a 76px field, 32px outlined chips 10px apart.\n   Colours use the shared card palette. The field's fill (black at 15%) has no token. */\n#card-shell#card-shell .chipsgroup, #card-shell#card-shell .tabsgroup { border: none; padding: 0; margin-bottom: 20px; }\n#card-shell#card-shell .chipsgroup h2, #card-shell#card-shell .tabsgroup h2 { font-weight: 500; line-height: 17px; padding: 3px 0; margin: 0 0 8px; color: var(--fg-2); }\n#card-shell#card-shell .chipsgroup textarea, #card-shell#card-shell .tabsgroup textarea { min-height: 76px; padding: 8px 12px; border-radius: 10px; line-height: 22px; border-color: var(--tonal); background: light-dark(rgba(0,0,0,.03), rgba(0,0,0,.15)); }\n#card-shell#card-shell .chips { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 8px; }\n#card-shell#card-shell .chipsgroup .hint, #card-shell#card-shell .tabsgroup .hint { margin: 8px 0 0; }\n/* The design keeps 20px between the title and the first section, as between sections. */\n#card-shell#card-shell h1 + .chipsgroup, #card-shell#card-shell h1 + .tabsgroup { margin-top: 20px; }\n/* Visual preference (Figma 2695-934191): the two tabs, then the open half under them. */\n#card-shell#card-shell .tabsgroup .segments { margin: 0 0 8px; }\n#card-shell#card-shell .chip { height: 32px; padding: 0 10px; border-radius: 10px; border-color: var(--tonal); background: transparent; color: inherit; font-weight: 500; line-height: 17px; }\n#card-shell#card-shell .chip[data-on=\"1\"] { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }\n/* The reference image row, per the Fine cut design (Figma 2695-933840): five 120:160 cells,\n   the Upload tile first. The tile's fill and dashed edge are white at 10% on the dark\n   palette and the same weight of black on the light one. */\n#card-shell#card-shell .imgs { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; padding-top: 8px; }\n#card-shell#card-shell .upload { aspect-ratio: 120 / 160; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; padding: 0; border: 1px dashed light-dark(rgba(0,0,0,.12), rgba(255,255,255,.1)); border-radius: 10px; background: light-dark(rgba(0,0,0,.05), rgba(255,255,255,.1)); color: inherit; font-weight: 500; font-size: 14px; line-height: 17px; }\n#card-shell#card-shell .upload svg { width: 24px; height: 24px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; }\n#card-shell#card-shell .upload[data-on=\"1\"] { border-style: solid; border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }\n#card-shell#card-shell .imgcell { position: relative; aspect-ratio: 120 / 160; overflow: hidden; border-radius: 10px; border: 1.5px solid light-dark(#000, #fff); }\n#card-shell#card-shell .imgcell img { display: block; width: 100%; height: 100%; object-fit: cover; }\n#card-shell#card-shell .imgcell .badge { position: absolute; left: 0; right: 0; bottom: 0; padding: 8px; font-size: 12px; line-height: 19px; color: #fff; background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,.6)); }\n#card-shell#card-shell .imgcell[data-status=\"failed\"] { border-color: #d08700; }\n/* A preset tile: the thumbnail edge to edge; picked, the picture's white edge and a check in\n   the top right corner, which draws over a light or a dark thumbnail alike. */\n#card-shell#card-shell .preset { position: relative; aspect-ratio: 120 / 160; overflow: hidden; padding: 0; border-radius: 10px; border: 1.5px solid transparent; background: light-dark(rgba(0,0,0,.05), rgba(255,255,255,.1)); }\n#card-shell#card-shell .preset img { display: block; width: 100%; height: 100%; object-fit: cover; }\n#card-shell#card-shell .preset[data-on=\"1\"] { border-color: light-dark(#000, #fff); }\n#card-shell#card-shell .preset[data-status=\"failed\"] { border-color: #d08700; }\n#card-shell#card-shell .preset .check { position: absolute; top: 8px; right: 8px; width: 16px; height: 16px; fill: none; stroke: #fff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; filter: drop-shadow(0 0 2px rgba(0,0,0,.6)); }\n#card-shell#card-shell .preset .badge { position: absolute; left: 0; right: 0; bottom: 0; padding: 8px; font-size: 12px; line-height: 19px; color: #fff; text-align: left; background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,.6)); }\n#card-shell#card-shell .imgacts { display: flex; gap: 8px; margin-top: 8px; }\n#card-shell#card-shell .imgacts button { padding: 4px 10px; font-size: 13px; background: transparent; color: inherit; }\n#card-shell#card-shell .imggroup .hint { margin-bottom: 0; }\n#card-shell#card-shell .actions { display: flex; gap: 12px; align-items: center; justify-content: flex-end; }\n/* The status line reads before the button it reports on, and the button keeps the right edge. */\n#card-shell#card-shell .actions .sub { margin: 0; order: -1; }\n#card-shell#card-shell button { font: inherit; padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(128,128,128,.5); cursor: pointer; }\n/* The primary button: the text colour filled, per the design's white-on-dark button. */\n#card-shell#card-shell button.go { min-width: 38px; height: 38px; padding: 0 12px; border-radius: 10px; border: none; background: var(--accent); color: var(--on-accent); font-weight: 500; line-height: 17px; }\n#card-shell#card-shell button.link { border: none; background: none; padding: 0; font-size: 12px; opacity: .8; text-decoration: underline; }\n#card-shell#card-shell button[disabled] { opacity: .6; cursor: default; }\n#card-shell#card-shell .done { opacity: .8; white-space: pre-wrap; }\n#card-shell#card-shell [hidden] { display: none; }\n\n/* A flow root keeps its children's outer margins inside its own height, so the height the\n   shell eases to is the height the card is laid out at once the shell lets go. */\n#card-shell#card-shell #card { display: flow-root; }\n/* The card's layout width never depends on whether it overflows the frame: the gutter is kept\n   either way and the body's right padding gives it back. While a height settles the frame\n   clips its overflow, so no scrollbar flickers in that gutter. */\n:root { scrollbar-gutter: stable; }\n:root[data-settling=\"1\"] { overflow: hidden; }\nbody { padding-right: max(0px, calc(16px - var(--gutter, 0px))); }\n#card-shell#card-shell[data-moving=\"1\"] { overflow: clip; transition: height 200ms cubic-bezier(0.25, 1, 0.5, 1); }\n@media (prefers-reduced-motion: reduce) { #card-shell#card-shell[data-moving=\"1\"] { transition: none; } }\n";
  var SHELL = "<div id=\"card-shell\"><div id=\"card\"></div></div>";
  // The fine cut is not a round, so its components never reach the card.
  var FINE_CUT = ["editing_preference_example", "editing_preference", "reference_image", "visual_preference_prompt"];
  var mounted = false;

  // Caption previews ship beside this file, so the widget's media policy admits them.
  function localize(output) {
    var copy = JSON.parse(JSON.stringify(output || {}));
    var data = copy.structuredContent && typeof copy.structuredContent === "object" ? copy.structuredContent : copy;
    if (data.card && Array.isArray(data.card.components)) {
      data.card.components = data.card.components.filter(function (component) {
        return !(component && FINE_CUT.indexOf(component.id) >= 0);
      });
    }
    var components = (data.card && data.card.components) || [];
    components.forEach(function (component) {
      (component.options || []).forEach(function (option) {
        var preview = option && option.preview;
        var match = preview && preview.kind === "video" && typeof preview.src === "string" && TILE_PATH.exec(preview.src);
        if (match && BASE) { preview.src = BASE + "caption-tiles/v1/" + match[1]; }
      });
    });
    return data;
  }

  function send(prompt) {
    if (typeof sendPrompt !== "function" || typeof prompt !== "string") { return Promise.resolve({ isError: true }); }
    sendPrompt(prompt);
    return Promise.resolve({});
  }

  function runCard() {

(function () {
  "use strict";
  // Built from the server's own constants, so the field cannot accept what the text
  // fallback calls illegal, or refuse what it calls legal.
  var COLOR_RE = /^#[0-9a-fA-F]{6}$/;
  var BREAK_RE = /[\n\r\u2028\u2029]/;
  var MAX_INPUT = 400;
  var MAX_VISUAL_PROMPT = 375;
  var root = document.getElementById("card");
  var hosted = null;
  var nextId = 1;
  var pending = {};
  var initialized = false;
  var canMessage = false;
  var view = null;

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) { node.className = cls; }
    // textContent, never a markup sink: every string here may have been written by a model.
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }

  function bridge() { return window.openai || window.mcpApps || null; }

  function rpc(method, params) {
    var id = "c" + nextId++;
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({ jsonrpc: "2.0", id: id, method: method, params: params || {} }, "*");
    }
    return id;
  }

  /** The tool result, from whichever channel this host actually uses. */
  function payload() {
    if (hosted && typeof hosted === "object") { return hosted; }
    var host = bridge() || {};
    var data = host.toolOutput || host.structuredContent || window.__MCP_TOOL_OUTPUT__;
    return data && typeof data === "object" ? data : null;
  }

  function adoptResult(data) {
    if (!data || typeof data !== "object") { return; }
    // A host may deliver the whole tool result or just its structured half.
    var result = data.structuredContent && typeof data.structuredContent === "object" ? data.structuredContent : data;
    if (!result.card || !Array.isArray(result.card.components)) { return; }
    hosted = Object.assign({}, result, { _meta: data._meta || result._meta });
    render();
  }

  window.addEventListener("message", function (event) {
    var data = event.data;
    if (event.source !== window.parent || !data || typeof data !== "object") { return; }
    if (typeof data.method === "string" && data.method.indexOf("tool-result") >= 0) {
      adoptResult(data.params);
      return;
    }
    if (data.id !== undefined && Object.prototype.hasOwnProperty.call(pending, data.id)) {
      var settle = pending[data.id];
      delete pending[data.id];
      settle(!data.error && !(data.result && data.result.isError), data.result, data.error);
      adoptResult(data.result);
      return;
    }
    if (data.id !== undefined && data.result) { adoptResult(data.result); return; }
    if (typeof data.type === "string" && data.type.indexOf("render") >= 0) { render(); }
  });

  // An ambiguous delivery stays pending; a timeout is not permission to send it again.
  function post(text, done, image) {
    var host = bridge();
    var helper = !canMessage && host && (host.sendFollowUpMessage || host.sendMessage);
    if (typeof helper === "function") {
      try {
        Promise.resolve(helper.call(host, host.sendFollowUpMessage ? { prompt: text } : text)).then(
          function (result) { done(!(result && result.isError)); },
          function () { done(false); }
        );
      } catch (err) { done(false); }
      return;
    }
    if ((initialized && !canMessage) || !window.parent || window.parent === window) { done(false); return; }
    var content = [{ type: "text", text: text }];
    if (image) { content.unshift(image); }
    var id = rpc("ui/message", { role: "user", content: content });
    pending[id] = done;
  }

  var state = Object.create(null);

  // Typing must not re-render the field it is typing into, so the button's gate is
  // refreshed in place instead of through render().
  var shown = null;
  var sendButton = null;
  var picks = []; // Every option on screen, so a pick is written back without a redraw.

  /**
   * The answers that may be written down: picked tokens only.
   *
   * A picked answer is one of a closed set the server published, so storing it records
   * which option was chosen and nothing else. A TYPED answer is the user's own words and
   * can carry anything they wrote - a name, an address, a key pasted by mistake, or a
   * draft they thought better of and never sent. It stays in this frame's memory for as
   * long as the frame lives and is written to no durable sink, because nothing here can
   * expire or delete what a host and a browser keep. The cost is named and small: a
   * remount reopens a typed field at the server's prefill instead of at what was being
   * typed. A picked answer still survives; a chip row holds none, so it is not stored.
   */
  function storableSelections() {
    var out = {};
    var groups = (shown && shown.components) || [];
    Object.keys(view.selections).forEach(function (id) {
      var typed = false;
      groups.forEach(function (group) {
        if (group && group.id === id && (isInput(group) || isChipRow(group))) { typed = true; }
      });
      if (!typed) { out[id] = view.selections[id]; }
    });
    return out;
  }

  // Host widget state belongs to this UI instance, not the whole conversation.
  function save() {
    // MCP Apps hosts can remount the frame without a ChatGPT widget-state bridge.
    // The server's per-result UUID keeps identical questions in separate views.
    if (view.storageKey) {
      try {
        window.localStorage.setItem(view.storageKey, JSON.stringify({
          selections: storableSelections(), status: view.submission && view.submission.status
        }));
      } catch (err) {}
    }
    var host = bridge();
    if (!host || typeof host.setWidgetState !== "function") { return; }
    var saved = host.widgetState || {};
    try {
      host.setWidgetState(Object.assign({}, saved, {
        privateContent: Object.assign({}, saved.privateContent, {
          // Never the view object itself: its selections is the live answer map and its
          // submission.text is the whole composed message, typed answers included. The
          // text is recomputed on restore, so only the status is worth keeping.
          aipDecisionCard: {
            cardKey: view.cardKey,
            storageKey: view.storageKey,
            selections: storableSelections(),
            submission: view.submission === null ? null : { status: view.submission.status }
          }
        })
      }));
    } catch (err) { /* In-memory state still protects this mounted card. */ }
  }

  function restore(card) {
    var key = JSON.stringify(card);
    shown = card;
    var data = payload();
    var host = bridge();
    var meta = (data && data._meta) || (host && host.toolResponseMetadata);
    var uuid = meta && meta.viewUUID;
    var storageKey = typeof uuid === "string" ? "aip:decision-card:" + uuid : null;
    if (view && view.cardKey === key && (!storageKey || view.storageKey === storageKey)) { return; }
    if (view && view.cardKey === key && !view.storageKey && storageKey &&
        (view.interacted || view.submission)) {
      // Late metadata must preserve the view whose acknowledgement is still in flight.
      view.storageKey = storageKey;
      save();
      return;
    }
    var saved = host && host.widgetState && host.widgetState.privateContent;
    saved = saved && saved.aipDecisionCard;
    if (!saved || saved.cardKey !== key || saved.storageKey !== storageKey) { saved = {}; }
    if (storageKey) {
      try {
        var stored = JSON.parse(window.localStorage.getItem(storageKey));
        if (stored && stored.selections && typeof stored.selections === "object") {
          saved = { selections: stored.selections, submission: stored.status ? { status: stored.status } : null };
        }
      } catch (err) {}
    }
    state = Object.create(null);
    card.components.forEach(function (group) {
      if (!group || typeof group.id !== "string") { return; }
      var values = saved.selections && saved.selections[group.id];
      if (!Array.isArray(values)) { return; }
      // A restored answer is re-vetted against the component as it arrives NOW, so a
      // question whose kind or options changed cannot resurrect an answer it no longer
      // accepts.
      var ok = isInput(group)
        ? values.length <= 1 && values.every(function (value) { return legalInput(group, value); })
        : (group.select === "multi" || values.length <= 1) &&
          values.every(function (value) {
            return (group.options || []).some(function (option) { return option && option.value === value; });
          });
      if (ok) { state[group.id] = values.slice(); }
    });
    var submission = saved.submission;
    if (submission && (["pending", "sent", "failed"].indexOf(submission.status) < 0 ||
        card.components.some(function (group) {
          if (!group || typeof group.id !== "string") { return false; }
          // Blank is a legal typed answer, and a typed answer is never restored, so a
          // field can say nothing about whether the card was already answered. Demanding
          // one here would discard a sent status on remount and let the user send twice.
          if (isInput(group) || isImage(group) || isChipRow(group)) { return false; }
          return !state[group.id] || (group.select !== "multi" && !blankAllowed(group) && state[group.id].length !== 1);
        }))) { submission = null; }
    if (submission) { submission.text = selectionMessage(card); }
    view = { cardKey: key, storageKey: storageKey, selections: state, submission: submission || null };
  }

  /** Seed each component from what the server said is already chosen, once. Without this
   *  a user who agrees with the current answer submits nothing and discards it. */
  function seed(card) {
    (card.components || []).forEach(function (group) {
      if (!group || typeof group.id !== "string" || state[group.id] !== undefined || isImage(group)) { return; }
      if (isInput(group)) {
        state[group.id] = legalInput(group, group.value) && group.value !== "" ? [group.value] : [];
        return;
      }
      state[group.id] = seedValues(group);
    });
  }

  function renderOption(group, option) {
    var picked = state[group.id] || [];
    var cell = el("div", "opt");
    cell.setAttribute("data-on", picked.indexOf(option.value) >= 0 ? "1" : "0");
    var label = el("label", null);
    var preview = option.preview;
    // Set by a chrome-free preview, which is a reach for the option rather than for a player.
    var selectOnClick = null;
    if (preview && preview.kind === "svg" && typeof preview.src === "string") {
      var img = document.createElement("img");
      img.src = preview.src;
      img.alt = "";
      // Not interactive content, so it stays INSIDE the label: for a visual style the
      // picture IS the option, and clicking it has always chosen it.
      label.appendChild(img);
    } else if (preview && preview.kind === "video" && typeof preview.src === "string") {
      var video = document.createElement("video");
      // Load a still preview, then play only when the user selects this option.
      video.preload = "auto";
      video.src = preview.src;
      video.muted = true;
      video.loop = true;
      video.playsInline = true;
      video.controls = false;
      video.autoplay = false;
      if (typeof preview.still === "number" && preview.still >= 0) { video.setAttribute("data-still", String(preview.still)); }
      // Clicking the preview selects and plays it. Keep it outside the label so native
      // controls, restored if playback is refused, cannot also select the option.
      video.setAttribute("data-select-on-click", "1");
      selectOnClick = function (input, adoptPick) {
        video.addEventListener("click", function () {
          if (video.getAttribute("data-select-on-click") !== "1" || releaseHeld(group, input, option.value)) { return; }
          input.checked = true;
          adoptPick();
        });
      };
      playInView(video);
      cell.appendChild(video);
    }
    var input = document.createElement("input");
    input.type = group.select === "multi" ? "checkbox" : "radio";
    input.name = inputName(group);
    input.checked = picked.indexOf(option.value) >= 0;
    /** Write whatever the control now reads back into the answer. Shared, because a chrome-
     *  free preview is a second way to reach the same option and must not be a second rule. */
    function adoptPick() {
      if (input.disabled) { return; }
      view.interacted = true;
      if (group.select === "multi") {
        var next = (state[group.id] || []).filter(function (v) { return v !== option.value; });
        if (input.checked) { next.push(option.value); }
        state[group.id] = next;
      } else {
        state[group.id] = input.checked ? [option.value] : [];
      }
      save();
      syncPicked();
      if (input.checked && cell.parentNode.querySelector("video")) { playSelectedPreview(video || null); }
    }
    input.addEventListener("change", adoptPick);
    releaseOnRepress(group, input, option.value);
    if (selectOnClick) { selectOnClick(input, adoptPick); }
    var name = el("span", "name", option.label || option.value);
    var head = el("div", null);
    head.appendChild(input);
    head.appendChild(name);
    if (option.recommended === true) { head.appendChild(el("span", "tag", "recommended")); }
    label.appendChild(head);
    if (option.description) {
      // The copy a host renders in place of the text result carries the suitability
      // guidance that separates one option from the next, so it has to be reachable.
      var why = el("div", "why", option.description);
      var more = el("button", "more", "More");
      more.addEventListener("click", function (event) {
        event.preventDefault();
        var open = why.getAttribute("data-open") === "1";
        why.setAttribute("data-open", open ? "0" : "1");
        more.textContent = open ? "More" : "Less";
      });
      label.appendChild(why);
      label.appendChild(more);
      mores.push({ why: why, more: more });
    }
    cell.appendChild(label);
    picks.push({ group: group, value: option.value, cell: cell, input: input });
    return cell;
  }

  /** Whether the card cannot be sent as it stands: mid-submission, or short an answer. */
  function sendBlocked(card) {
    return !!(view.submission && view.submission.status === "pending") || imageBusy() || unanswered(card);
  }

  /** Update selections in place so buffered and playing previews survive a pick. */
  function syncPicked() {
    picks.forEach(function (pick) {
      var on = (state[pick.group.id] || []).indexOf(pick.value) >= 0;
      pick.cell.setAttribute("data-on", on ? "1" : "0");
      pick.input.checked = on;
    });
    syncReveals();
    syncGates();
    if (sendButton && shown) { sendButton.disabled = sendBlocked(shown); }
    scheduleSize();
  }

  /** Whether the card still lacks an answer it cannot be sent without.
   *  A blank field is a legal answer, so it never blocks the button. An ILLEGAL one
   *  does: a colour the receiving side cannot parse is worse sent than not sent. */
  function unanswered(card) {
    return (card.components || []).some(function (group) {
      if (!group || typeof group.id !== "string" || isImage(group)) { return false; }
      // A field nobody can see is not a question, so it cannot be short an answer.
      if (isInput(group)) {
        return revealShown(card, group) && !legalInput(group, (state[group.id] || [])[0] || "");
      }
      return group.select !== "multi" && !blankAllowed(group) && !(state[group.id] || []).length;
    });
  }

  function renderGroup(group) {
    if (tabsOf(shown, group)) { return renderTabsGroup(group); }
    if (isImage(group)) { return renderImage(group); }
    if (isInput(group)) {
      var row = renderInput(group);
      if (group.narrowed !== false || !group.narrowing_hint) { return row; }
      var held = el("div", null);
      held.appendChild(row);
      held.appendChild(el("div", "warn", group.narrowing_hint));
      return held;
    }
    var display = displayOf(group);
    if (display && display.kind === "switch") { return renderSwitchGroup(group, display); }
    if (display && display.kind === "gate") { return renderGateGroup(group, display); }
    if (display && display.kind === "rows") { return renderRowsGroup(group, display); }
    if (display && display.kind === "chips") { return renderChipsGroup(group, display); }
    var box = el("div", "group");
    box.appendChild(el("h2", null, group.label || group.id));
    // The HINT, never the note: the note names a canvas, a face box and a worker, which is
    // what the agent needs to describe the risk and is nothing a user can act on.
    if (group.narrowed === false && group.narrowing_hint) {
      box.appendChild(el("div", "warn", group.narrowing_hint));
    }
    var opts = el("div", "opts");
    (group.options || []).forEach(function (option) {
      if (option && typeof option.value === "string") { opts.appendChild(renderOption(group, option)); }
    });
    box.appendChild(opts);
    attachReveals(box, group);
    return box;
  }

  /** An answered card in words. An empty MULTI-select is stated as an empty list, never
   *  as "no answer": the receiving contracts read an omitted feature list as EVERY toggle
   *  on, so a silent nothing would turn on exactly what the user just turned off. */
  function selectionMessage(card) {
    var lines = ["I picked:"];
    (card.components || []).forEach(function (group) {
      if (!group || typeof group.id !== "string") { return; }
      var picked = state[group.id] || [];
      if (isChipRow(group)) { return; } // It only typed into its field, which answers for it.
      if (isImage(group)) {
        lines.push("- " + (group.label || group.id) + " (" + group.id + "): " + imageAnswer(group));
        return;
      }
      if (isInput(group)) {
        // A hidden conditional field was never asked, so it answers nothing even when the
        // user typed into it before moving the picker off the option that revealed it.
        if (!revealShown(card, group)) { picked = []; }
        // Quoted, and said to be verbatim, because nothing downstream vets a typed
        // answer: whatever reaches the agent here is what the user gets.
        lines.push("- " + (group.label || group.id) + " (" + group.id + "): " + (picked.length > 0
          ? "typed VERBATIM, use exactly as written: \"" + picked[0] + "\""
          : "left blank - no answer"));
        return;
      }
      var answer;
      if (picked.length > 0) {
        answer = picked.map(function (value) {
          var option = (group.options || []).find(function (item) { return item.value === value; });
          return option && option.label && option.label !== value ? value + " (" + option.label + ")" : value;
        }).join(", ");
      } else if (group.select === "multi") {
        answer = "none of them - submit this as an EMPTY LIST, not as an omitted field";
      } else {
        answer = blankAnswer(group);
      }
      lines.push("- " + (group.label || group.id) + " (" + group.id + "): " + answer);
    });
    return lines.join("\n");
  }

  /** Every exit from draw() leaves a different height, so the report hangs off the wrapper. */
  function render() { draw(); scheduleSize(); }

  function draw() {
    var data = payload();
    var card = data && data.card;
    root.textContent = "";
    if (!card || !Array.isArray(card.components)) {
      root.appendChild(el("p", "note", "This card could not read its contents. The tool's text result carries the same choices."));
      return;
    }
    restore(card);
    seed(card);
    sendButton = null;
    picks = [];
    reveals = [];
    mores = [];
    gates = [];
    forgetPreviews();
    var sent = view.submission && view.submission.status === "sent";
    var submitting = view.submission && view.submission.status === "pending";
    root.appendChild(el("h1", null, card.title || "Your choices"));
    if (card.note) { root.appendChild(el("p", "note", card.note)); }
    // A conditional field carries the sentence itself, beside the box it describes, so the
    // card's foot speaks only for the fields that are always on screen.
    var typed = card.components.filter(function (group) {
      return group && isInput(group) && !revealedElsewhere(group) && !tabsOf(card, group);
    });
    card.components.forEach(function (group) {
      if (group && typeof group.id === "string" && !revealedElsewhere(group)) {
        root.appendChild(renderGroup(group));
      }
    });
    // One sentence for the whole card: repeated per question it was five of the same line.
    if (typed.length > 0) {
      root.appendChild(el("p", "hint", TYPED_HINT +
        (typed.some(function (group) { return group.kind === "color"; }) ? " Write a colour as #rrggbb." : "")));
    }
    // Saving the image is part of sending: the answer is read when the save returns.
    if (sent || submitting || imageBusy()) {
      // Every control that edits an answer, segment buttons included: one still live beside
      // "Sent" shows the user an answer the chat never received, with no way to send it.
      root.querySelectorAll("input, textarea, button.seg, button.img, button.preset, button.chip").forEach(function (control) { control.disabled = true; });
    }
    // The answered card says so IN the action row. A line appended under it would make the
    // document taller than the height the host measured before the click, and the overflow
    // is what scrolls inside the frame.
    var actions = el("div", "actions");
    var send = el("button", "go", "Send my preference");
    send.disabled = sendBlocked(card);
    var status = el("span", "sub", sent ? "Added to your message. Press Enter to send it." :
      submitting ? "Waiting for the chat to confirm receipt..." :
      imageBusy() && !picking ? "Saving the image..." :
      view.submission ? "Not added to your message. Press Send again, or type your choices in the chat." : "");
    send.addEventListener("click", function () {
      if (send.disabled || (view.submission && view.submission.status !== "failed")) { return; }
      var submittedView = view;
      // A picture is saved first, and a refused save sends nothing: the answer never names
      // an image the server did not take.
      withSavedImage(card, function () {
        var text = selectionMessage(card);
        submittedView.submission = { status: "pending", text: text };
        save();
        render();
        post(text, function (ok) {
          submittedView.submission.status = ok ? "sent" : "failed";
          if (view === submittedView) { save(); render(); }
        }, imageBlock());
      });
    });
    // An answered card drops the button rather than disabling it: the row then costs one
    // line of status text, which is never taller than the button it replaces.
    sendButton = sent ? null : send;
    if (!sent) { actions.appendChild(send); } else { var change = el("button", "change", "Change"); change.addEventListener("click", function () { view.submission = null; save(); render(); }); actions.appendChild(change); }
    actions.appendChild(status);
    root.appendChild(actions);
    if (submitting) { root.appendChild(fallback(view.submission.text, actions)); }
  }


  /** A component the user types into rather than picks from. */
  function isInput(group) { return group.kind === "text" || group.kind === "color"; }

  function inputLimit(group) {
    return group.authority === "server" && group.id === "visual_preference_prompt" ? MAX_VISUAL_PROMPT : MAX_INPUT;
  }

  /** The card's half of the same predicate the server states in its text fallback. */
  function legalInput(group, value) {
    if (typeof value !== "string" || value.length > inputLimit(group)) { return false; }
    if (group.kind === "color") { return value === "" || COLOR_RE.test(value); }
    return !BREAK_RE.test(value);
  }

  /** Each drawn field's writer by component id, so a shortcut outside the field can type
   *  into it through the same path a keystroke takes. Redrawing a field replaces its entry. */
  var fieldWriters = Object.create(null);

  /** A typed answer, on one row: its question, a swatch when the answer is a colour, and
   *  the text box. A bordered block per question costs a card with five of them more
   *  height than a host frame gives it.
   *
   *  A BARE field drops the row label and takes the full width: it is drawn inside the
   *  group of the picker that revealed it, where the option already names what it is for
   *  and a 34% side label would read as a fourth question. */
  function renderInput(group, bare) {
    var wrap = el("div", bare ? "field bare" : "field");
    if (!bare) { wrap.appendChild(el("span", "rowlabel", group.label || group.id)); }
    var current = (state[group.id] || [])[0] || "";
    var multiline = group.multiline === true;
    var box = document.createElement(multiline ? "textarea" : "input");
    if (multiline) { box.setAttribute("rows", "3"); } else { box.type = "text"; }
    box.name = "g_" + group.id;
    // The question beside the field names it visually and not programmatically; without
    // this a screen reader announces an unlabelled edit box.
    box.setAttribute("aria-label", String(group.label || group.id));
    box.setAttribute("maxlength", String(inputLimit(group)));
    if (typeof group.placeholder === "string") { box.placeholder = group.placeholder; }
    box.value = current;
    var swatch = null;
    if (group.kind === "color") {
      swatch = document.createElement("input");
      swatch.type = "color";
      swatch.name = "s_" + group.id;
      swatch.setAttribute("aria-label", String(group.label || group.id) + " colour picker");
      swatch.value = COLOR_RE.test(current) ? current : "#000000";
      wrap.appendChild(swatch);
    }
    function commit(value, echo) {
      // A card mid-submission or already sent has had its answer read; a late edit would
      // sit on screen as the answer while the chat holds the earlier one.
      if (view.submission && view.submission.status !== "failed") { box.value = (state[group.id] || [])[0] || ""; return; }
      view.interacted = true;
      // A submitted answer is one line of a line-joined message, so a break typed into a
      // multi-line box folds to a space on the way into the answer. The box keeps what was
      // typed: reflowing it under the user mid-sentence would be the edit they did not make.
      // The hint under the box says this happens, because the message calls the answer
      // verbatim and that promise has to be true of the text the answer actually carries.
      var answer = multiline ? value.split(BREAK_RE).join(" ") : value;
      state[group.id] = answer === "" ? [] : [answer];
      box.setAttribute("data-bad", legalInput(group, answer) ? "0" : "1");
      if (echo && swatch && COLOR_RE.test(value)) { swatch.value = value; }
      save();
      if (sendButton && shown) { sendButton.disabled = sendBlocked(shown); }
    }
    box.addEventListener("input", function () { commit(box.value, true); });
    fieldWriters[group.id] = { box: box, write: function (value) { box.value = value; commit(value, true); } };
    // The text box is what the answer IS, so a swatch pick writes through it rather than
    // holding a second value the message would then have to choose between.
    if (swatch) {
      swatch.addEventListener("input", function () {
        box.value = swatch.value;
        commit(swatch.value, false);
      });
    }
    wrap.appendChild(box);
    return wrap;
  }

  /** The composed message, kept one click away rather than printed. An unacknowledged send
   *  still has to leave the user something to paste, but a card that grows while it waits
   *  scrolls inside the frame the host already sized. The opener joins the action row; the
   *  message itself is returned hidden, for the caller to place. */
  function fallback(text, row) {
    var reveal = el("button", "link", "Show the message");
    var held = el("div", null);
    held.hidden = true;
    held.appendChild(el("p", "note", "If this answer does not appear in the chat, check there before sending it manually."));
    held.appendChild(el("pre", "done", text));
    reveal.addEventListener("click", function (event) {
      event.preventDefault();
      held.hidden = !held.hidden;
      reveal.textContent = held.hidden ? "Show the message" : "Hide the message";
      scheduleSize();
    });
    row.appendChild(reveal);
    return held;
  }


  /** A component the user answers with a picture. */
  function isImage(group) { return group.kind === "image"; }

  // The one picture this frame holds: { mime, bytes, data, sha256, url, status, path, task },
  // where url is the data: URL of data that the thumbnail draws.
  // status is "ready" (shrunk, not saved), "saving", "saved" or "failed" (the save was
  // refused; the file is kept so a second send retries it).
  var picture = null;
  var picking = false;
  var pickSeq = 0;
  var imageNote = "";
  var intent = false;
  var canCallTools = false;
  var canSendImage = false;

  var IMAGE_UPLOAD_TOOL = "upload_reference_image";
  var IMAGE_QUALITY = 0.85;
  var PLUS_ICON = "M12 5v14M5 12h14";

  /** Whether the frame can save a picture here. Without server tools it can only record intent. */
  function imagePicker() { return canCallTools; }

  /** An image group on this card, if any: the card has at most one reference image. */
  function imageGroupOf(card) {
    return ((card && card.components) || []).find(function (group) { return group && isImage(group); }) || null;
  }

  /** The picture's answer line, stated so the agent knows the path is staged, not accepted. */
  function imageAnswer(group) {
    if (tabAway(shown, group)) { return "not asked - the user described the look in words instead"; }
    if (!imagePicker()) {
      return intent ? "I'll attach a reference image" : "none - continue without one";
    }
    var saved = presetPick(group) || picture;
    if (saved && saved.status === "saved") {
      return group.id + "=" + saved.path + " (commit task " + saved.task + ", staged, not yet accepted)";
    }
    return "none - continue without one";
  }

  /** Whether the image half holds the card back: mid-shrink or mid-save. */
  function imageBusy() {
    return picking || !!(picture && picture.status === "saving") || !!(chosenPreset && chosenPreset.status === "saving");
  }

  function forgetPicture() { picture = null; }

  function hex(buffer) {
    return Array.prototype.map.call(new Uint8Array(buffer), function (byte) {
      return ("0" + byte.toString(16)).slice(-2);
    }).join("");
  }

  function base64(buffer) {
    var bytes = new Uint8Array(buffer);
    var out = "";
    for (var i = 0; i < bytes.length; i += 32768) {
      out += String.fromCharCode.apply(null, bytes.subarray(i, i + 32768));
    }
    return window.btoa(out);
  }

  /** Decode through createImageBitmap where the frame has it, else through an image element. */
  function decodeImage(file) {
    if (typeof window.createImageBitmap === "function") { return window.createImageBitmap(file); }
    return new Promise(function (resolve, reject) {
      var reader = new window.FileReader();
      reader.onerror = function () { reject(new Error("decode")); };
      reader.onload = function () {
        var img = document.createElement("img");
        img.onload = function () { resolve(img); };
        img.onerror = function () { reject(new Error("decode")); };
        img.src = reader.result;
      };
      reader.readAsDataURL(file);
    });
  }

  function encodeCanvas(canvas, type) {
    return new Promise(function (resolve) { canvas.toBlob(resolve, type, IMAGE_QUALITY); });
  }

  /** Draw the picked file no larger than the component allows, as WebP, or JPEG where the
   *  frame cannot encode WebP (it hands back PNG instead of failing). */
  function shrinkImage(file, group) {
    return decodeImage(file).then(function (source) {
      var width = source.width || source.naturalWidth || 0;
      var height = source.height || source.naturalHeight || 0;
      if (!width || !height) { throw new Error("decode"); }
      var scale = Math.min(1, group.max_long_side / Math.max(width, height));
      var canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(width * scale));
      canvas.height = Math.max(1, Math.round(height * scale));
      canvas.getContext("2d").drawImage(source, 0, 0, canvas.width, canvas.height);
      if (typeof source.close === "function") { source.close(); }
      return encodeCanvas(canvas, "image/webp").then(function (blob) {
        return blob && blob.type === "image/webp" ? blob : encodeCanvas(canvas, "image/jpeg");
      });
    }).then(function (blob) {
      if (!blob || (blob.type !== "image/webp" && blob.type !== "image/jpeg")) { throw new Error("decode"); }
      if (blob.size > group.max_bytes) { throw new Error("size"); }
      return blob.arrayBuffer().then(function (buffer) {
        return window.crypto.subtle.digest("SHA-256", buffer).then(function (digest) {
          var data = base64(buffer);
          return {
            mime: blob.type, bytes: blob.size, data: data, sha256: hex(digest),
            url: "data:" + blob.type + ";base64," + data, status: "ready", path: null, task: null
          };
        });
      });
    });
  }

  /** A picked file: checked against the accepted types, shrunk, and held. A cancelled
   *  picker delivers no file and leaves the answer as it was. */
  function adoptFile(group, file) {
    if (!file || imageLocked()) { return; }
    if ((group.accept || []).indexOf(file.type) < 0) {
      imageNote = "Pick a PNG, JPEG or WebP image.";
      render();
      return;
    }
    var seq = ++pickSeq;
    picking = true;
    imageNote = "";
    render();
    shrinkImage(file, group).then(function (next) {
      if (seq !== pickSeq) { return; }
      picking = false;
      imageNote = "";
      forgetPicture();
      // An upload and a preset are one choice: the new picture replaces a picked preset.
      chosenPreset = null;
      picture = next;
      view.interacted = true;
      render();
    }, function (err) {
      if (seq !== pickSeq) { return; }
      picking = false;
      imageNote = err && err.message === "size"
        ? "This image is still too large after shrinking. Try a smaller one."
        : "This file could not be read as an image. Try another.";
      render();
    });
  }

  /** A card mid-send or already sent has had its answer read, so the picture is fixed. */
  function imageLocked() {
    return !!(view.submission && view.submission.status !== "failed") || !!(picture && picture.status === "saving") ||
      !!(chosenPreset && chosenPreset.status === "saving");
  }

  /** The tool's text block, as JSON where it is JSON and as its raw text where it is not. */
  function toolBody(result) {
    var content = result && Array.isArray(result.content) ? result.content : [];
    var block = content.find(function (item) { return item && item.type === "text"; });
    var text = block && typeof block.text === "string" ? block.text : "";
    try { return { json: JSON.parse(text), text: text }; } catch (err) { return { json: null, text: text }; }
  }

  /** The saved result, if the tool's text block is one: it has to name the bytes sent. */
  function uploadedImage(result) {
    var saved = toolBody(result).json;
    if (!saved || typeof saved.path !== "string" || typeof saved.task_id !== "string") { return null; }
    return picture && saved.sha256 === picture.sha256 ? saved : null;
  }

  /** What the user is told when the server refuses the image, by the refusal's code. */
  var REFUSAL_REASONS = {
    invalid_base64: "The image did not arrive intact.",
    image_digest_mismatch: "The image did not arrive intact.",
    image_too_large: "The image is too large to save.",
    image_type_mismatch: "The image type was not recognised.",
    image_too_many_pixels: "The image has too many pixels to save.",
    retry_commit: "The project is busy saving something else.",
    locked_by_task: "The project is busy with another task.",
    image_staging_unavailable: "Saving images is unavailable right now.",
    preset_unavailable: "This example image is unavailable right now.",
    unknown_preset: "This example image is no longer offered."
  };

  /** A host whose server does not serve the upload tool answers as if it did not exist:
   *  the gate is closed there, which is the same as a host that relays no tools. */
  function toolMissing(result, error, tool) {
    var said = (error && error.message) || toolBody(result).text || "";
    return said.indexOf("Tool " + (tool || IMAGE_UPLOAD_TOOL) + " not found") >= 0;
  }

  /**
   * A refused save. A refusal the server calls retryable, and anything that is not a
   * refusal at all (a lost reply, a transport error), keeps the file for the next send. A
   * refusal of the image itself cannot succeed on retry, so the file is dropped and the
   * user picks another. A missing tool turns the tile into the intent tile.
   */
  function refuseImage(held, result, error) {
    if (toolMissing(result, error)) {
      canCallTools = false;
      forgetPicture();
      imageNote = "";
      render();
      return;
    }
    var refusal = toolBody(result).json;
    var coded = !!(refusal && typeof refusal.code === "string");
    // The budget refusal names itself by next_action, as commit_workspace's does; a lock
    // conflict by its next_data state, with the image already staged. Both are capacity,
    // and the server names an image by its digest, so sending the same file again is safe.
    var state = refusal && refusal.next_data && refusal.next_data.state;
    var reason = (refusal && (REFUSAL_REASONS[refusal.code] || REFUSAL_REASONS[refusal.next_action] ||
      REFUSAL_REASONS[state])) || "The image was not saved.";
    if (coded && refusal.retryable !== true) {
      forgetPicture();
      imageNote = reason + " Pick another image, or send without one.";
    } else {
      held.status = "failed";
      imageNote = reason + " It is still here: send again to retry, or remove it.";
    }
    render();
  }

  /**
   * Save the picture into the project, then send. The answer never names an image the
   * server has not accepted a write for: a refused save keeps the file and sends nothing,
   * so the next press of the send button retries the save rather than the message.
   */
  function withSavedImage(card, proceed) {
    var group = imageGroupOf(card);
    // A closed tab is not asked: its picture stays in the frame and is neither saved nor sent.
    if (!group || tabAway(card, group) || !imagePicker()) { proceed(); return; }
    var preset = presetPick(group);
    if (preset) {
      if (preset.status === "saved") { proceed(); } else { withSavedPreset(card, preset, proceed); }
      return;
    }
    if (!picture || picture.status === "saved") { proceed(); return; }
    var held = picture;
    held.status = "saving";
    render();
    var id = rpc("tools/call", {
      name: IMAGE_UPLOAD_TOOL,
      arguments: { project_id: card.project_id, mime_type: held.mime, data: held.data, sha256: held.sha256 }
    });
    pending[id] = function (ok, result, error) {
      if (picture !== held) { return; }
      var saved = ok ? uploadedImage(result) : null;
      if (!saved) {
        refuseImage(held, result, error);
        return;
      }
      imageNote = "";
      held.status = "saved";
      held.path = saved.path;
      held.task = saved.task_id;
      proceed();
    };
  }

  /** The image block that travels with the answer, where the chat can show one. */
  function imageBlock() {
    return canSendImage && picture && picture.status === "saved" && !tabAway(shown, imageGroupOf(shown))
      ? { type: "image", data: picture.data, mimeType: picture.mime }
      : null;
  }

  function plusIcon() {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", PLUS_ICON);
    svg.appendChild(path);
    return svg;
  }

  var PICTURE_BADGE = {
    ready: "Saved when you send", saving: "Saving...", saved: "Saved", failed: "Not saved"
  };

  /** The tile row: the Upload tile first, or the picked picture with Replace and Remove.
   *  BARE draws it with no box or heading, as a tab of a section that names it. */
  function renderImage(group, bare) {
    var box = el("div", bare ? "imgbare" : "group imggroup");
    if (!bare) { box.appendChild(el("h2", null, group.label || group.id)); }
    if (!imagePicker()) { return renderImageIntent(box, group); }
    var file = document.createElement("input");
    file.type = "file";
    file.name = "f_" + group.id;
    file.hidden = true;
    file.setAttribute("accept", (group.accept || []).join(","));
    file.addEventListener("change", function () {
      var picked = file.files && file.files[0];
      file.value = "";
      adoptFile(group, picked);
    });
    box.appendChild(file);
    var grid = el("div", "imgs");
    if (picture) {
      var cell = el("div", "imgcell");
      cell.setAttribute("data-status", picture.status);
      var thumb = document.createElement("img");
      thumb.src = picture.url;
      thumb.alt = "Your reference image";
      cell.appendChild(thumb);
      cell.appendChild(el("span", "badge", PICTURE_BADGE[picture.status] || ""));
      grid.appendChild(cell);
    } else {
      var tile = el("button", "upload img");
      tile.type = "button";
      tile.setAttribute("aria-label", "Upload a reference image");
      tile.appendChild(plusIcon());
      tile.appendChild(el("span", null, picking ? "Reading..." : "Upload"));
      tile.disabled = picking;
      tile.addEventListener("click", function () { if (!imageLocked()) { file.click(); } });
      grid.appendChild(tile);
    }
    renderPresets(group, grid);
    box.appendChild(grid);
    if (picture) { box.appendChild(renderImageActions(file)); }
    if (imageNote) { box.appendChild(el("p", "warn", imageNote)); }
    return box;
  }

  function renderImageActions(file) {
    var row = el("div", "imgacts");
    var replace = el("button", "img", "Replace");
    replace.type = "button";
    replace.addEventListener("click", function () { if (!imageLocked()) { file.click(); } });
    var remove = el("button", "img", "Remove");
    remove.type = "button";
    remove.addEventListener("click", function () {
      if (imageLocked()) { return; }
      // A replacement still being read is part of what the user removed: it must not land after.
      pickSeq++;
      picking = false;
      forgetPicture();
      imageNote = "";
      render();
    });
    replace.disabled = remove.disabled = imageLocked();
    row.appendChild(replace);
    row.appendChild(remove);
    return row;
  }

  /** A host that cannot run the save: the tile records that the user will attach one in the
   *  chat, which is intent, never an image. */
  function renderImageIntent(box, group) {
    var grid = el("div", "imgs");
    var tile = el("button", "upload img");
    tile.type = "button";
    tile.setAttribute("aria-pressed", intent ? "true" : "false");
    tile.setAttribute("data-on", intent ? "1" : "0");
    tile.appendChild(plusIcon());
    tile.appendChild(el("span", null, "Attach in chat"));
    tile.addEventListener("click", function () {
      if (imageLocked()) { return; }
      intent = !intent;
      view.interacted = true;
      render();
    });
    grid.appendChild(tile);
    box.appendChild(grid);
    box.appendChild(el("p", "hint", "This chat cannot take an upload from the card. Choose this, send, and then " +
      "attach the image in the chat."));
    return box;
  }


  // The preset the user picked: { id, status, path, task }, status as for the picture.
  var chosenPreset = null;
  var PRESET_TOOL = "use_reference_preset";
  var CHECK_ICON = "M5 12.5l4.5 4.5L19 7.5";

  /** The well-formed presets this image component offers, in the server's order. */
  function presetsOf(group) {
    return (group && Array.isArray(group.presets) ? group.presets : []).filter(function (preset) {
      return preset && typeof preset.id === "string" && typeof preset.thumb_url === "string" &&
        /^https:[/][/]/.test(preset.thumb_url);
    });
  }

  /** The picked preset, if the shown card still offers it. */
  function presetPick(group) {
    if (!chosenPreset) { return null; }
    return presetsOf(group).some(function (preset) { return preset.id === chosenPreset.id; }) ? chosenPreset : null;
  }

  /** Pick a preset, or put back the one already picked. Picking drops an uploaded picture,
   *  and a picture still being read, since the two are one choice. */
  function togglePreset(preset) {
    if (imageLocked()) { return; }
    pickSeq++;
    picking = false;
    forgetPicture();
    imageNote = "";
    chosenPreset = chosenPreset && chosenPreset.id === preset.id
      ? null
      : { id: preset.id, status: "ready", path: null, task: null };
    view.interacted = true;
    render();
  }

  /** The saved result, if the tool's text block is one for a preset copy. */
  function copiedPreset(result) {
    var saved = toolBody(result).json;
    return saved && typeof saved.path === "string" && typeof saved.task_id === "string" ? saved : null;
  }

  /** Copy the picked preset into the project, then send; a refused copy sends nothing. */
  function withSavedPreset(card, held, proceed) {
    held.status = "saving";
    render();
    var id = rpc("tools/call", { name: PRESET_TOOL, arguments: { project_id: card.project_id, preset_id: held.id } });
    pending[id] = function (ok, result, error) {
      if (chosenPreset !== held) { return; }
      var saved = ok ? copiedPreset(result) : null;
      if (!saved) {
        refusePreset(held, result, error);
        return;
      }
      imageNote = "";
      held.status = "saved";
      held.path = saved.path;
      held.task = saved.task_id;
      proceed();
    };
  }

  /** A refused copy: kept for a retry where the server says one can succeed, else dropped. */
  function refusePreset(held, result, error) {
    if (toolMissing(result, error, PRESET_TOOL)) {
      chosenPreset = null;
      imageNote = "Example images are unavailable here. Upload your own, or send without one.";
      render();
      return;
    }
    var refusal = toolBody(result).json;
    var state = refusal && refusal.next_data && refusal.next_data.state;
    var reason = (refusal && (REFUSAL_REASONS[refusal.code] || REFUSAL_REASONS[refusal.next_action] ||
      REFUSAL_REASONS[state])) || "The image was not saved.";
    if (refusal && typeof refusal.code === "string" && refusal.retryable !== true) {
      chosenPreset = null;
      imageNote = reason + " Pick another image, or send without one.";
    } else {
      held.status = "failed";
      imageNote = reason + " It is still picked: send again to retry.";
    }
    render();
  }

  function checkIcon() {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("class", "check");
    var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", CHECK_ICON);
    svg.appendChild(path);
    return svg;
  }

  /** One tile per preset, after the Upload tile; the picked one is outlined and checked. */
  function renderPresets(group, grid) {
    var picked = presetPick(group);
    presetsOf(group).forEach(function (preset) {
      var on = !!picked && picked.id === preset.id;
      var tile = el("button", "preset");
      tile.type = "button";
      tile.setAttribute("aria-pressed", on ? "true" : "false");
      tile.setAttribute("aria-label", String(preset.label || preset.id));
      tile.setAttribute("data-on", on ? "1" : "0");
      tile.setAttribute("data-preset", preset.id);
      if (on) { tile.setAttribute("data-status", picked.status); }
      var thumb = document.createElement("img");
      thumb.src = preset.thumb_url;
      thumb.alt = "";
      thumb.decoding = "async";
      tile.appendChild(thumb);
      if (on) { tile.appendChild(checkIcon()); }
      if (on && (picked.status === "saving" || picked.status === "failed")) {
        tile.appendChild(el("span", "badge", PICTURE_BADGE[picked.status]));
      }
      tile.disabled = imageLocked();
      tile.addEventListener("click", function () { togglePreset(preset); });
      grid.appendChild(tile);
    });
  }


  /** One sentence for every typed question on screen, wherever it is shown. */
  var TYPED_HINT = "Typed answers are used exactly as written; leave any blank if you have none.";
  /** The same promise, kept honest where a break cannot survive: an answer travels as one
   *  line of the submitted message, so the box says so rather than folding in silence. */
  var MULTILINE_HINT = TYPED_HINT + " A line break becomes a space.";

  /** The revealed fields currently drawn, so a pick flips them without a redraw. */
  var reveals = [];
  /** Every clipped-description opener, with the text it opens, for the measurement below. */
  var mores = [];

  /** The picker a field hangs off, or null when this card does not carry it - in which case
   *  the field is an ordinary question and is drawn the way it always was. */
  function revealOwner(card, group) {
    var want = group && group.reveal;
    if (!want || typeof want.component !== "string") { return null; }
    var groups = (card && card.components) || [];
    for (var i = 0; i < groups.length; i++) {
      var candidate = groups[i];
      if (candidate && candidate.id === want.component && !isInput(candidate)) { return candidate; }
    }
    return null;
  }

  /** Whether a conditional field is being asked at all right now. */
  function revealShown(card, group) {
    if (tabAway(card, group)) { return false; }
    var owner = revealOwner(card, group);
    if (!owner) { return true; }
    return (state[owner.id] || []).indexOf(group.reveal.value) >= 0;
  }

  /** Draw every field this picker reveals, inside the picker's own box and under its tiles.
   *  Hidden is the default: the field appears where the option that needs it was chosen. */
  function attachReveals(box, group) {
    var card = shown;
    ((card && card.components) || []).forEach(function (other) {
      if (!other || !isInput(other) || revealOwner(card, other) !== group) { return; }
      var held = el("div", "reveal");
      held.appendChild(renderInput(other, true));
      // The card's one sentence about typed answers, moved to the field it now describes:
      // at the card's foot it would be a promise about a box nobody can see.
      held.appendChild(el("p", "hint", other.multiline === true ? MULTILINE_HINT : TYPED_HINT));
      held.hidden = !revealShown(card, other);
      reveals.push({ group: other, node: held });
      box.appendChild(held);
    });
  }

  /** Whether this component is drawn inside another group rather than at the card's top. */
  function revealedElsewhere(group) {
    return (isInput(group) && (revealOwner(shown, group) !== null || chippedElsewhere(group))) || tabbedElsewhere(group);
  }

  /** Flip the conditional fields to match the picks now held. The typed words stay in the
   *  hidden field, so returning to the option that revealed it returns what was written. */
  function syncReveals() {
    reveals.forEach(function (item) {
      item.node.hidden = !revealShown(shown, item.group);
    });
  }

  /** The one observer every preview shares: a fresh one per clip would be eight of them.
   *  Disconnected on the draw that discards the tiles it was watching. */
  var inView = null;
  var selectedPreview = null;
  /** Without a published still, show caption ink near the end, before the closing frames clear it. */
  var PREVIEW_STILL_PROGRESS = 0.83;

  function pauseAtPreviewFrame(video) {
    if (typeof video.pause === "function") { video.pause(); }
    if (!(Number.isFinite(video.duration) && video.duration > 0)) { return; }
    var still = parseFloat(video.getAttribute("data-still"));
    video.currentTime = still >= 0 && still < video.duration ? still : video.duration * PREVIEW_STILL_PROGRESS;
  }

  /** Selection is a user gesture, so retry even when the host refused automatic playback. */
  function playPreview(video) {
    var started = typeof video.play === "function" ? video.play() : null;
    if (started && typeof started.catch === "function") {
      started.catch(function (err) {
        // Switching selections or leaving the viewport intentionally interrupts buffering.
        if (!err || err.name !== "AbortError") { restoreControls(video); }
      });
    }
  }

  /** A selection without a video clears playback and leaves every preview on its still. */
  function playSelectedPreview(video) {
    selectedPreview = video;
    root.querySelectorAll(".opt video").forEach(function (clip) {
      clip.autoplay = clip === video;
      if (clip !== video) { pauseAtPreviewFrame(clip); }
    });
    if (video) {
      video.currentTime = 0;
      playPreview(video);
    }
  }

  /** Resume only the selected preview on screen; keep every unselected preview paused. */
  function playInView(video) {
    video.addEventListener("loadedmetadata", function () {
      if (selectedPreview !== video) { pauseAtPreviewFrame(video); }
    });
    // A viewer who asked the system for less motion is asking for this too. They get the
    // controls back, so the style is still inspectable - just not moving unasked.
    if (stillPreferred()) { video.autoplay = false; restoreControls(video); return; }
    if (typeof window.IntersectionObserver !== "function") { return; }
    if (!inView) {
      inView = new window.IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var clip = entry.target;
          if (entry.isIntersecting && selectedPreview === clip) {
            playPreview(clip);
          } else if (typeof clip.pause === "function") {
            clip.pause();
          }
        });
      });
    }
    inView.observe(video);
  }

  /** Whether this viewer has asked the system to keep motion down. */
  function stillPreferred() {
    if (typeof window.matchMedia !== "function") { return false; }
    try { return !!window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (err) { return false; }
  }

  /** Give one clip its controls back, and take away the click that stood in for them.
   *  The two are exclusive: a press on a control strip must not also arm the option. */
  function restoreControls(video) {
    video.controls = true;
    video.setAttribute("data-select-on-click", "0");
  }

  /** Let go of the previews a redraw is about to discard. */
  function forgetPreviews() {
    if (inView && typeof inView.disconnect === "function") { inView.disconnect(); }
    selectedPreview = null;
  }

  /** Drop the opener from any tile whose description was never clipped, and put it back on
   *  one that is clipped again.
   *
   *  Only a laid-out document can answer this, so it runs from the measuring frame rather
   *  than from the draw - the same frame that follows every reflow, because a frame the
   *  host narrows turns a description that fitted into one that no longer does. It defaults
   *  to leaving the button alone: a frame that reports no measurements keeps today's card,
   *  and a tile already opened keeps the Less that closes it. */
  function trimMore() {
    mores.forEach(function (pair) {
      if (pair.why.getAttribute("data-open") === "1") { pair.more.hidden = false; return; }
      var full = pair.why.scrollHeight;
      var box = pair.why.clientHeight;
      if (typeof full !== "number" || typeof box !== "number" || box <= 0) { return; }
      // One pixel of slack: a sub-pixel line height rounds the two apart on a tile that fits.
      pair.more.hidden = full <= box + 1;
    });
  }


  /** A field's tab pairing, or null when the card does not carry the component it names. */
  function tabsOf(card, group) {
    var tabs = group && isInput(group) ? group.tabs : null;
    if (!tabs || typeof tabs.component !== "string") { return null; }
    var other = pairedWith(card, tabs);
    return other ? tabs : null;
  }

  /** The component a pairing's first tab draws. */
  function pairedWith(card, tabs) {
    return ((card && card.components) || []).find(function (other) {
      return other && other.id === tabs.component && !isInput(other);
    }) || null;
  }

  /** The tabbed field that holds this component as its other tab, or null. */
  function tabOwner(card, group) {
    if (!group || isInput(group)) { return null; }
    return ((card && card.components) || []).find(function (other) {
      var tabs = tabsOf(card, other);
      return !!tabs && tabs.component === group.id;
    }) || null;
  }

  /** Which tab of this field is open: "component" (the first) unless the user opened its own. */
  function openTab(field) {
    return view && view.tabs && view.tabs[field.id] === "self" ? "self" : "component";
  }

  /** Whether a closed tab hides this component, so it is not asked and answers nothing. */
  function tabAway(card, group) {
    if (!group) { return false; }
    if (tabsOf(card, group)) { return openTab(group) !== "self"; }
    var owner = tabOwner(card, group);
    return !!owner && openTab(owner) === "self";
  }

  /** Whether this component is drawn inside a tabbed field's section rather than on its own. */
  function tabbedElsewhere(group) {
    return tabOwner(shown, group) !== null;
  }

  /** The section: the field's label, the two tabs, and whichever half is open. */
  function renderTabsGroup(field) {
    var tabs = tabsOf(shown, field);
    var box = el("div", "group tabsgroup");
    box.appendChild(el("h2", null, field.label || field.id));
    var bar = el("div", "segments");
    bar.setAttribute("role", "tablist");
    bar.setAttribute("aria-label", String(field.label || field.id));
    [["component", tabs.component_label], ["self", tabs.label]].forEach(function (spec) {
      var on = openTab(field) === spec[0];
      var tab = el("button", "seg", String(spec[1] || ""));
      tab.type = "button";
      tab.setAttribute("role", "tab");
      tab.setAttribute("data-on", on ? "1" : "0");
      tab.setAttribute("aria-selected", on ? "true" : "false");
      tab.addEventListener("click", function () {
        if (tab.disabled || on || (view.submission && view.submission.status !== "failed")) { return; }
        var next = Object.assign({}, view.tabs);
        next[field.id] = spec[0];
        view.tabs = next;
        render();
      });
      bar.appendChild(tab);
    });
    box.appendChild(bar);
    if (openTab(field) === "self") {
      box.appendChild(renderInput(field, true));
      box.appendChild(el("p", "hint", field.multiline === true ? MULTILINE_HINT : TYPED_HINT));
      return box;
    }
    var other = pairedWith(shown, tabs);
    box.appendChild(isImage(other) ? renderImage(other, true) : renderGroup(other));
    return box;
  }


  /** The display a picker asked for, or null for the tile grid a picker gets by default. */
  function displayOf(group) {
    var display = group && group.display;
    return display && typeof display.kind === "string" && !isInput(group) ? display : null;
  }

  function optionOf(group, value) {
    return (group.options || []).find(function (option) { return option && option.value === value; }) || null;
  }

  /** What a picker opens on when the caller preselected nothing: the token a switch rests
   *  on, the row a segmented picker starts from, or - for a gate - open with nothing picked. */
  function seedValues(group) {
    var display = displayOf(group);
    // A chip row is a typing shortcut that holds no pick, so a preselected token it draws
    // becomes its words in an empty field, where the user sees and sends it, not a token.
    if (display && display.kind === "chips") {
      seedChipField(group, display);
      return [];
    }
    if (Array.isArray(group.selected) && group.selected.length > 0) { return group.selected.slice(); }
    if (!display) { return []; }
    if (display.kind === "switch") { return [display.initial]; }
    if (display.kind === "rows" && typeof display.initial === "string") { return [display.initial]; }
    return [];
  }

  /** Whether nothing picked is itself an answer for this picker rather than a missing one. */
  function blankAllowed(group) {
    var display = displayOf(group);
    return !!display && (display.kind === "gate" || display.kind === "chips");
  }

  /** On a picker where nothing picked is itself an answer, a second press on the picked tile
   *  clears it, the way back to that answer without closing the gate around it. A radio
   *  fires no change when pressed again, so this listens for the click and reads the answer
   *  as it stood before it: the tile was already held only if the state still names it. */
  function releaseOnRepress(group, input, value) {
    input.addEventListener("click", function () { releaseHeld(group, input, value); });
  }

  /** Clear the pick if this tile already holds it, and say whether it did. The tile's
   *  preview is a second way to press it, so it asks here before it selects. */
  function releaseHeld(group, input, value) {
    if (!blankAllowed(group) || group.select === "multi") { return false; }
    if (input.disabled || (state[group.id] || [])[0] !== value) { return false; }
    view.interacted = true;
    input.checked = false;
    state[group.id] = [];
    save();
    syncPicked();
    playSelectedPreview(null);
    return true;
  }

  /** The native group name for a picker's inputs. A card may repeat a question, and radios
   *  sharing one name are one group to the browser, which would uncheck the first copy to
   *  check the second; so each drawn copy gets its own name over the one shared answer. */
  function inputName(group) {
    var base = "g_" + group.id;
    var taken = Object.create(null);
    root.querySelectorAll("input").forEach(function (input) { taken[input.name] = true; });
    var name = base;
    for (var n = 2; taken[name]; n++) { name = base + "-" + n; }
    return name;
  }

  /** The answer line for a single-select with nothing picked. Auto has no token, so the
   *  line has to say in words that the field is to be left unset rather than filled. */
  function blankAnswer(group) {
    var display = displayOf(group);
    return blankAllowed(group)
      ? "nothing picked - Auto: leave " + group.id + " unset so the run chooses"
      : "no answer";
  }

  /** The pictograms a row may wear, as 24-unit paths: stroked, or filled where SOLID names
   *  them (the Rough cut pair, which the design draws as filled shapes). A name on the wire, a drawing
   *  only here: model-authored copy reaches this document and a name cannot carry markup. */
  var ICONS = {
    clean: "M19 7.05859C18.9999 5.90325 18.0863 5 17 5H7C5.91373 5 5.00013 5.90325 5 7.05859V13.917C5 15.0725 5.91365 15.9766 7 15.9766H9.5L9.62012 15.9834C9.89684 16.0168 10.1492 16.1649 10.3135 16.3945L11.9316 18.6582L13.71 16.3643L13.7852 16.2773C13.9721 16.0861 14.2293 15.9766 14.5 15.9766H17C18.0863 15.9766 19 15.0725 19 13.917V7.05859ZM21 13.917C21 16.1402 19.2274 17.9766 17 17.9766H14.9902L13.0986 20.418C12.5211 21.1636 11.4296 21.1888 10.8145 20.5156L10.6982 20.3721L8.98633 17.9766H7C4.77264 17.9766 3 16.1402 3 13.917V7.05859C3.00013 4.83547 4.77272 3 7 3H17C19.2273 3 20.9999 4.83547 21 7.05859V13.917ZM11 8C11 7.44772 11.4477 7 12 7C12.5523 7 13 7.44772 13 8V13C13 13.5523 12.5523 14 12 14C11.4477 14 11 13.5523 11 13V8ZM7 9.5C7 8.94772 7.44772 8.5 8 8.5C8.55228 8.5 9 8.94772 9 9.5V11.5C9 12.0523 8.55228 12.5 8 12.5C7.44772 12.5 7 12.0523 7 11.5V9.5ZM15 9.5C15 8.94772 15.4477 8.5 16 8.5C16.5523 8.5 17 8.94772 17 9.5V11.5C17 12.0523 16.5523 12.5 16 12.5C15.4477 12.5 15 12.0523 15 11.5V9.5Z",
    keep: "M11.1289 10.002C11.3546 9.98218 11.6289 10.1509 12.1768 10.4883L13.0938 11.0527C13.602 11.3657 13.8565 11.5222 13.9434 11.7236C14.0191 11.8997 14.0191 12.1003 13.9434 12.2764C13.8565 12.4778 13.602 12.6343 13.0938 12.9473L12.1768 13.5117C11.6289 13.8491 11.3546 14.0178 11.1289 13.998C10.9321 13.9807 10.7521 13.8789 10.6348 13.7188C10.5003 13.535 10.5 13.2114 10.5 12.5645V11.4355C10.5 10.7886 10.5003 10.465 10.6348 10.2812C10.7521 10.1211 10.9321 10.0193 11.1289 10.002ZM13.5996 2C15.8398 2 16.9608 1.99957 17.8164 2.43555L18.0918 2.58984C18.7183 2.97413 19.2289 3.52512 19.5645 4.18359L19.6406 4.34766C19.9999 5.18397 20 6.30006 20 8.40039V15.5996L19.9932 17.084C19.9744 18.2757 19.9041 19.0391 19.6406 19.6523L19.5645 19.8164C19.2289 20.4749 18.7183 21.0259 18.0918 21.4102L17.8164 21.5645C16.9608 22.0004 15.8398 22 13.5996 22H10.4004C8.16018 22 7.03924 22.0004 6.18359 21.5645C5.43109 21.181 4.81902 20.5689 4.43555 19.8164C4.10861 19.1747 4.02728 18.3839 4.00684 17.084L4 15.5996V8.40039C4 6.16018 3.99957 5.03924 4.43555 4.18359C4.81902 3.43109 5.43109 2.81902 6.18359 2.43555C7.03924 1.99957 8.16018 2 10.4004 2H13.5996ZM10.4004 4C9.24728 4 8.50222 4.00155 7.93555 4.04785C7.39231 4.09224 7.19068 4.16739 7.0918 4.21777C6.71554 4.40951 6.40951 4.71554 6.21777 5.0918C6.16739 5.19068 6.09224 5.39231 6.04785 5.93555C6.00155 6.50222 6 7.24728 6 8.40039V15.5996C6 16.7527 6.00155 17.4978 6.04785 18.0645C6.09224 18.6077 6.16739 18.8093 6.21777 18.9082C6.40951 19.2845 6.71554 19.5905 7.0918 19.7822C7.19068 19.8326 7.39231 19.9078 7.93555 19.9521C8.50222 19.9984 9.24728 20 10.4004 20H13.5996C14.7527 20 15.4978 19.9984 16.0645 19.9521C16.6077 19.9078 16.8093 19.8326 16.9082 19.7822C17.2845 19.5905 17.5905 19.2845 17.7822 18.9082C17.8326 18.8093 17.9078 18.6077 17.9521 18.0645C17.9984 17.4978 18 16.7527 18 15.5996V8.40039C18 7.24728 17.9984 6.50222 17.9521 5.93555C17.9078 5.39231 17.8326 5.19068 17.7822 5.0918C17.5905 4.71554 17.2845 4.40951 16.9082 4.21777C16.8093 4.16739 16.6077 4.09224 16.0645 4.04785C15.4978 4.00155 14.7527 4 13.5996 4H10.4004Z",
    captions: "M3 6.5A2.5 2.5 0 0 1 5.5 4h13A2.5 2.5 0 0 1 21 6.5v11a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5zM10 10.2a2.2 2.2 0 1 0 0 3.6M17 10.2a2.2 2.2 0 1 0 0 3.6",
    music: "M9 18V6l10-2v11M9 18a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0zM19 15a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z",
    sfx: "M4 9.5v5h3.5L12 18.5v-13L7.5 9.5zM15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"
  };

  var SOLID = { clean: true, keep: true };

  function icon(name) {
    if (!Object.prototype.hasOwnProperty.call(ICONS, name)) { return null; }
    var ns = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(ns, "svg");
    svg.setAttribute("class", SOLID[name] === true ? "ico solid" : "ico");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    var path = document.createElementNS(ns, "path");
    path.setAttribute("d", ICONS[name]);
    svg.appendChild(path);
    return svg;
  }

  /** One row: a pictogram, the question with a line under it, and a control on the right.
   *  The line is returned so the caller can keep it saying what the control now means. */
  function row(iconName, label, control) {
    var line = el("div", "row");
    var glyph = iconName ? icon(iconName) : null;
    if (glyph) { line.appendChild(glyph); }
    var text = el("div", "rowtext");
    text.appendChild(el("div", "rowlabel", label));
    var desc = el("div", "rowdesc", "");
    // An eased line goes back to its own height once it has arrived. See easeLine.
    desc.addEventListener("transitionend", function (event) {
      if (event.propertyName === "height") { desc.style.height = ""; desc.removeAttribute("data-easing"); }
    });
    text.appendChild(desc);
    line.appendChild(text);
    line.appendChild(control);
    return { node: line, desc: desc };
  }

  /** Swap a row's line in step with the fold beside it. The two lines can wrap to different
   *  heights, and a line that jumped while the fold eased would push the card the wrong way
   *  for a frame; easing it over the fold's time and curve keeps the card moving one way.
   *  A line not yet laid out, or a viewer who asked for less motion, gets the text at once. */
  function easeLine(desc, text) {
    if (desc.textContent === text) { return; }
    var from = desc.getBoundingClientRect().height;
    desc.style.height = "";
    desc.textContent = text;
    var to = desc.getBoundingClientRect().height;
    if (!from || !to || from === to || stillPreferred()) { desc.removeAttribute("data-easing"); return; }
    desc.setAttribute("data-easing", "1");
    desc.style.height = from + "px";
    void desc.offsetHeight;
    desc.style.height = to + "px";
  }

  /** Name a row's control by its visible text and let the whole row flip it. The ids are
   *  unique on the page even when a card repeats a component, so each control names its own
   *  row. A press on the control itself is left to the control, or it would flip twice. */
  function bindRow(line, control, idBase) {
    var base = "row-" + String(idBase).replace(/[^A-Za-z0-9_-]/g, "_");
    var id = base;
    for (var n = 2; document.getElementById(id + "-label"); n++) { id = base + "-" + n; }
    var label = line.node.querySelector(".rowlabel");
    label.id = id + "-label";
    line.desc.id = id + "-desc";
    control.input.removeAttribute("aria-label");
    control.input.setAttribute("aria-labelledby", label.id);
    control.input.setAttribute("aria-describedby", line.desc.id);
    line.node.addEventListener("click", function (event) {
      var target = event.target;
      if (control.input.disabled || (target && target.closest && target.closest(".switch"))) { return; }
      control.toggle();
    });
  }

  /** A toggle. The input is what the answer is; the knob beside it is only what is drawn. */
  function switchControl(name, label, on, onChange) {
    var wrap = el("label", "switch");
    var input = document.createElement("input");
    input.type = "checkbox";
    input.setAttribute("role", "switch");
    input.setAttribute("aria-label", String(label));
    input.name = name;
    input.checked = on;
    input.addEventListener("change", function () {
      if (input.disabled) { return; }
      onChange(input.checked);
    });
    wrap.appendChild(input);
    wrap.appendChild(el("span", "knob"));
    /** Flip it as a press on the input would, for a press that landed elsewhere on its row. */
    function toggle() {
      input.checked = !input.checked;
      onChange(input.checked);
    }
    return { node: wrap, input: input, toggle: toggle };
  }

  /** The rows whose line has to follow a pick made elsewhere on the card, such as a tile
   *  under an open gate. Rebuilt on every draw. */
  var gates = [];

  function syncGates() {
    gates.forEach(function (gate) { gate.describe(); });
  }

  /** A two-token question as one row with a switch. The answer is always a token: a
   *  switch has no blank state, which is why the component names the one it rests on. */
  function renderSwitchGroup(group, display) {
    var box = el("div", "group rowgroup");
    var control = switchControl("g_" + group.id, group.label || group.id, held(group) === display.on, function (checked) {
      view.interacted = true;
      state[group.id] = [checked ? display.on : display.off];
      save();
      syncPicked();
    });
    var line = row(display.icon, group.label || group.id, control.node);
    bindRow(line, control, group.id);
    function describe() {
      var option = optionOf(group, held(group));
      line.desc.textContent = option && option.description ? option.description : "";
      line.node.setAttribute("data-on", held(group) === display.on ? "1" : "0");
      // A card may carry the same question twice; each copy reads the one answer.
      control.input.checked = held(group) === display.on;
    }
    describe();
    gates.push({ group: group, describe: describe });
    box.appendChild(line.node);
    return box;
  }

  function held(group) { return (state[group.id] || [])[0]; }

  /** A toggle over a tile grid. Off submits the one token; on shows the grid, and on with
   *  no tile picked is Auto - an answer the component names in words, not a missing one.
   *  Opening always lands on Auto: the gate keeps no tile from before it closed, so a pick
   *  cannot outlive the card or the options it was made against. */
  function renderGateGroup(group, display) {
    var box = el("div", "group rowgroup gategroup");
    var grid = el("div", "opts");
    // The hint and the tiles fold away under the row rather than leaving the document, so
    // the card can ease between its two heights instead of jumping. See .fold in the style.
    var fold = el("div", "fold");
    var folded = el("div", "foldin");
    fold.appendChild(folded);
    var control = switchControl("t_" + group.id, group.label || group.id, held(group) !== display.off, function (checked) {
      view.interacted = true;
      state[group.id] = checked ? [] : [display.off];
      save();
      syncPicked();
      // Neither position holds a pick, and a pick is what plays a preview.
      playSelectedPreview(null);
    });
    var line = row(display.icon, group.label || group.id, control.node);
    bindRow(line, control, group.id);
    function open(isOpen) {
      fold.setAttribute("data-open", isOpen ? "1" : "0");
      // Still in the document while folded, so no tile may take Tab or be read out.
      if (isOpen) {
        fold.removeAttribute("inert");
        fold.removeAttribute("aria-hidden");
      } else {
        fold.setAttribute("inert", "");
        fold.setAttribute("aria-hidden", "true");
      }
    }
    function describe() {
      var value = held(group);
      var option = optionOf(group, value);
      var isOpen = value !== display.off;
      var flipping = fold.getAttribute("data-open") === (isOpen ? "0" : "1");
      control.input.checked = isOpen;
      open(isOpen);
      line.node.setAttribute("data-on", isOpen ? "1" : "0");
      var text = isOpen ? (option ? (option.label || value) : display.blank) : (option && option.description ? option.description : "");
      if (flipping) { easeLine(line.desc, text); } else { line.desc.textContent = text; }
    }
    box.appendChild(line.node);
    // The HINT, never the note: the note is the agent's copy of what was not checked.
    if (group.narrowed === false && group.narrowing_hint) {
      folded.appendChild(el("div", "warn", group.narrowing_hint));
    }
    (group.options || []).forEach(function (option) {
      if (option && typeof option.value === "string" && option.value !== display.off) {
        grid.appendChild(renderOption(group, option));
      }
    });
    folded.appendChild(grid);
    box.appendChild(fold);
    attachReveals(box, group);
    describe();
    gates.push({ group: group, describe: describe });
    return box;
  }

  /** A single-select drawn as rows of radios, each row its own box. A row is one option,
   *  wearing that option's copy, or several options held as a segmented control that shows
   *  only while its row is picked. Picking a segmented row keeps the held value when the
   *  row already holds it and otherwise lands on the row's own initial. An option no row
   *  names still reaches the user, as a tile under the rows. The control and its line fold
   *  open and shut rather than appearing, and a folded one is inert: out of the tab order
   *  and the accessibility tree, not merely drawn at zero height. */
  function renderRowsGroup(group, display) {
    var box = el("div", "group rowsgroup");
    // One name for this copy's rows; a tile drawn under them asks before this box is on the
    // page, so it lands in the same native group.
    var name = inputName(group);
    var named = Object.create(null);
    var lines = [];
    (display.rows || []).forEach(function (spec, index) {
      var values = Array.isArray(spec.values) ? spec.values.filter(function (value) { return optionOf(group, value); }) : null;
      var single = values ? null : optionOf(group, spec.value);
      if (values ? values.length === 0 : !single) { return; }
      (values || [single.value]).forEach(function (value) { named[value] = true; });
      var radio = document.createElement("input");
      radio.type = "radio";
      radio.name = name;
      radio.value = values ? values[0] : single.value;
      var label = values ? spec.label : (single.label || single.value);
      var line = row(spec.icon, label, radio);
      // The whole row is the target a person reaches for, and the line under the label is
      // what a screen reader should announce with the radio.
      // A press anywhere on the row picks it; picking is idempotent, so the press that lands
      // on the radio itself and then fires its change settles on the same answer. The
      // segments sit outside the row, so a press on a tab never reaches this.
      bindRow(line, { input: radio, toggle: function () { radio.checked = true; choose(); } }, group.id + "-" + index);
      var cell = el("div", "rowbox");
      cell.appendChild(line.node);
      var segments = null;
      var level = null;
      var fold = null;
      var tabs = [];
      if (values) {
        line.desc.textContent = spec.description || "";
        segments = el("div", "segments");
        segments.setAttribute("role", "group");
        segments.setAttribute("aria-label", String(label));
        values.forEach(function (value) {
          var option = optionOf(group, value);
          var tab = el("button", "seg", option.label || value);
          tab.type = "button";
          tab.addEventListener("click", function () {
            if (tab.disabled || radio.disabled) { return; }
            pick(value);
          });
          tabs.push({ node: tab, value: value });
          segments.appendChild(tab);
        });
        level = el("div", "rowdesc segdesc", "");
        level.id = line.desc.id.replace(/-desc$/, "-level");
        segments.setAttribute("aria-describedby", level.id);
        // The fold animates its row track between 0fr and 1fr; the inner box is what clips.
        fold = el("div", "segfold");
        var folded = el("div", "segfoldin");
        folded.appendChild(segments);
        folded.appendChild(level);
        fold.appendChild(folded);
        // Drawn in its first position, so a card never opens on a fold mid-animation.
        setFold(fold, holds());
        cell.appendChild(fold);
      } else {
        // A row may name its own line; an empty one draws the label alone.
        line.desc.textContent = typeof spec.description === "string" ? spec.description : (single.description || "");
      }
      function holds() { return values ? values.indexOf(held(group)) >= 0 : held(group) === single.value; }
      function choose() {
        if (radio.disabled || !radio.checked) { return; }
        if (!holds()) { pick(values ? (values.indexOf(spec.initial) >= 0 ? spec.initial : values[0]) : single.value); }
      }
      radio.addEventListener("change", choose);
      function describe() {
        var on = holds();
        radio.checked = on;
        cell.setAttribute("data-on", on ? "1" : "0");
        if (!values) { return; }
        setFold(fold, on);
        tabs.forEach(function (tab) {
          var active = on && tab.value === held(group);
          tab.node.setAttribute("data-on", active ? "1" : "0");
          tab.node.setAttribute("aria-pressed", active ? "true" : "false");
        });
        // A folding line keeps its words while it shuts, so the fold never jumps to empty first.
        if (!on) { return; }
        var option = optionOf(group, held(group));
        level.textContent = option && option.description ? option.description : "";
      }
      lines.push(describe);
      box.appendChild(cell);
    });
    function pick(value) {
      view.interacted = true;
      state[group.id] = [value];
      save();
      syncPicked();
    }
    var rest = (group.options || []).filter(function (option) {
      return option && typeof option.value === "string" && !named[option.value];
    });
    if (rest.length > 0) {
      var grid = el("div", "opts");
      rest.forEach(function (option) { grid.appendChild(renderOption(group, option)); });
      box.appendChild(grid);
    }
    function describeAll() { lines.forEach(function (describe) { describe(); }); }
    describeAll();
    gates.push({ group: group, describe: describeAll });
    attachReveals(box, group);
    return box;
  }

  /** Opens or shuts a row's fold. Shut is inert and hidden from a screen reader as well as
   *  collapsed, because zero height alone leaves the tabs reachable by Tab. */
  function setFold(fold, open) {
    fold.setAttribute("data-open", open ? "1" : "0");
    if (open) {
      fold.removeAttribute("inert");
      fold.removeAttribute("aria-hidden");
    } else {
      fold.setAttribute("inert", "");
      fold.setAttribute("aria-hidden", "true");
    }
  }

  /** The id of the typed field a chip row names, or null. */
  function chipFieldId(group) {
    var display = displayOf(group);
    return display && display.kind === "chips" && typeof display.field === "string" ? display.field : null;
  }

  /** The typed field this chip row draws above its chips, or null. A card that repeats the
   *  row draws the field once, in the first copy: two boxes over one answer would disagree. */
  function chipField(card, group) {
    var id = chipFieldId(group);
    var groups = (card && card.components) || [];
    var owner = groups.find(function (other) { return other && chipFieldId(other) === id; });
    if (id === null || owner !== group) { return null; }
    return groups.find(function (other) { return other && isInput(other) && other.id === id; }) || null;
  }

  /** Whether a chip row on this card draws this typed field inside its own box. */
  function chippedElsewhere(group) {
    return isInput(group) && ((shown && shown.components) || []).some(function (other) {
      return other && chipFieldId(other) === group.id;
    });
  }

  /** Carry a chip row's first drawn preselection into its field as that chip's words, unless
   *  the field already holds an answer, which always wins. Runs before the field seeds or
   *  after it, so a field the server prefilled is checked here as well. */
  function seedChipField(group, display) {
    var fieldId = typeof display.field === "string" ? display.field : null;
    var token = (group.selected || []).find(function (value) { return (display.values || []).indexOf(value) >= 0; });
    var option = token === undefined ? null : optionOf(group, token);
    if (fieldId === null || !option || (state[fieldId] || []).length > 0) { return; }
    var field = ((shown && shown.components) || []).find(function (other) {
      return other && isInput(other) && other.id === fieldId;
    });
    if (!field || (typeof field.value === "string" && field.value !== "")) { return; }
    state[fieldId] = [String(option.label || token)];
  }

  /** Whether this picker is a chip row: shortcuts that type into a field and answer nothing. */
  function isChipRow(group) {
    var display = displayOf(group);
    return !!display && display.kind === "chips";
  }

  /** The field text after a chip adds its words: the words alone into an empty field, else
   *  appended after what is there, so a chip never erases typing. Words already present are
   *  not added twice, and an addition that would overrun the field's limit is not made. */
  function chipFill(current, words, limit) {
    var kept = current.trimEnd();
    if (kept === "") { return words; }
    if (kept.toLowerCase().indexOf(words.toLowerCase()) >= 0) { return current; }
    var next = kept + (/[.,;:!?]$/.test(kept) ? " " : ", ") + words;
    return next.length > limit ? current : next;
  }

  /** Example wordings drawn as shortcut chips under the field they suggest for. A chip types
   *  its words into the field through the field's own input path, the way a keystroke does,
   *  and holds no state of its own: the field is the only answer, and the user can still
   *  edit what a chip wrote. */
  function renderChipsGroup(group, display) {
    var box = el("div", "group chipsgroup");
    box.appendChild(el("h2", null, group.label || group.id));
    var field = chipField(shown, group);
    if (field) {
      var placeholder = typeof display.placeholder === "string" ? display.placeholder : field.placeholder;
      box.appendChild(renderInput(Object.assign({}, field, { placeholder: placeholder }), true));
    }
    var line = el("div", "chips");
    line.setAttribute("role", "group");
    line.setAttribute("aria-label", String(group.label || group.id));
    var fieldId = chipFieldId(group);
    (display.values || []).forEach(function (value) {
      var option = optionOf(group, value);
      if (!option) { return; }
      var words = String(option.label || value);
      var chip = el("button", "chip", words);
      chip.type = "button";
      if (option.description) { chip.title = option.description; }
      chip.addEventListener("click", function () {
        if (chip.disabled || (view.submission && view.submission.status !== "failed")) { return; }
        var writer = fieldId === null ? null : fieldWriters[fieldId];
        if (!writer) { return; }
        var box = writer.box;
        var next = chipFill(box.value, words, Number(box.getAttribute("maxlength")) || Infinity);
        if (next !== box.value) { writer.write(next); }
        box.focus();
        if (typeof box.setSelectionRange === "function") { box.setSelectionRange(box.value.length, box.value.length); }
      });
      line.appendChild(chip);
    });
    box.appendChild(line);
    // The promise the card's foot makes for a typed answer, kept where this field is drawn.
    if (field) { box.appendChild(el("p", "hint", field.multiline === true ? MULTILINE_HINT : TYPED_HINT)); }
    return box;
  }


  /* The body border box is the measurement. The root element is stretched to fill the
     frame, so a height read from it could only ever grow. Nothing is sent unless the
     numbers actually moved, so the observer cannot feed itself. */
  var sentSize = null;
  var sizeQueued = false;

  function reportSize() {
    sizeQueued = false;
    // The one laid-out moment this document gets, and the only place a tile's description
    // can be told from the box clipping it. It runs first so the height reported below is
    // the height of the card AFTER any opener it dropped. See decision-card-reveal-script.
    trimMore();
    // A redraw queues this measurement before the shell's own observer has seen the new
    // height, and the read below lays the card out: pin the shell first, or the host is told
    // the height the card is about to move to, a frame before it moves there.
    // See decision-card-height-motion.
    followHeight();
    // Nothing delivered yet: the fallback line is not a height to give a host. See
    // decision-card-height-motion.
    if (!payload()) { return; }
    var body = document.body;
    var rect = body && typeof body.getBoundingClientRect === "function" ? body.getBoundingClientRect() : null;
    // A frame that has not been laid out yet measures zero, which is no height to ask a host for.
    var height = body ? Math.ceil(Math.max(body.scrollHeight || 0, (rect && rect.height) || 0)) : 0;
    if (height <= 0 || !window.parent || window.parent === window) { return; }
    // The body spans the frame less the scrollbar gutter the card keeps; a host that sizes the
    // frame's width from this report must be told the frame's, or each report would shrink it.
    var width = Math.ceil(Math.max(body.scrollWidth || 0, (rect && rect.width) || 0)) + heldGutter;
    if (sentSize && sentSize.width === width && sentSize.height === height) { return; }
    sentSize = { width: width, height: height };
    window.parent.postMessage({ jsonrpc: "2.0", method: "ui/notifications/size-changed", params: sentSize }, "*");
  }

  /** A size sent before the host acknowledged ui/initialize may have been dropped, and the
      dedupe would never offer that number again. Forget it and say it once more. */
  function resendSize() {
    sentSize = null;
    scheduleSize();
  }

  /** Coalesce a burst of observer callbacks into the one measurement that follows them. */
  function scheduleSize() {
    if (sizeQueued) { return; }
    sizeQueued = true;
    if (typeof window.requestAnimationFrame === "function") { window.requestAnimationFrame(reportSize); }
    else { reportSize(); }
  }

  if (typeof window.ResizeObserver === "function" && document.body) {
    new window.ResizeObserver(scheduleSize).observe(document.body);
  }


  var heightShell = document.getElementById("card-shell");
  var heightContent = document.getElementById("card");
  /** The height the shell last came to rest at or is easing toward. Null before the first
      layout, which is drawn where it lands: there is no earlier height to move from. */
  var shownHeight = null;

  function reducedMotion() {
    return typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  var SIZE_PROPERTY = /^(height|max-height|min-height|grid-template-rows|margin|padding|block-size|max-block-size)/;

  /** Whether some part of the card is animating its own size right now. */
  function regionMoving() {
    if (typeof heightContent.getAnimations !== "function") { return false; }
    return heightContent.getAnimations({ subtree: true }).some(function (motion) {
      if (motion.playState !== "running") { return false; }
      if (typeof motion.transitionProperty === "string") { return SIZE_PROPERTY.test(motion.transitionProperty); }
      var frames = motion.effect && typeof motion.effect.getKeyframes === "function" ? motion.effect.getKeyframes() : [];
      return frames.some(function (frame) { return Object.keys(frame).some(function (key) { return SIZE_PROPERTY.test(key.replace(/[A-Z]/g, function (c) { return "-" + c.toLowerCase(); })); }); });
    });
  }

  /** Let go of the pinned height once the shell has arrived, so the card is laid out by its
      content again and the next change starts from a natural height. */
  function settleHeight() {
    heightShell.removeAttribute("data-moving");
    heightShell.style.height = "";
  }

  /** Whether a height transition on the shell is still under way. A retarget cancels the
      transition it replaces, and that cancellation arrives after the new one has started:
      it must not let go of the height the new one is moving to. */
  function shellStillMoving() {
    if (typeof heightShell.getAnimations !== "function") { return false; }
    return heightShell.getAnimations().some(function (motion) {
      return motion.playState === "running" && motion.transitionProperty === "height";
    });
  }

  var frameRoot = document.documentElement;
  /** How many frames in a row the frame must stand still, with nothing moving, before a card
      it still clips is allowed to scroll: long enough for a host's resize to land, short
      enough that a capped frame's scrollbar comes back without anyone waiting for it. */
  var SETTLE_FRAMES = 10;
  var settleQueued = false;
  var settleViewport = -1;
  var settleStill = 0;
  /** The gutter's width in px; the frame-size report adds it back to the body's width. */
  var heldGutter = 0;

  /** The scrollbar gutter this frame keeps, handed back from the body's right padding. The
      root's clientWidth does not count a kept gutter in Chrome, so it is read off the body,
      which spans the frame less that gutter. */
  function holdGutter() {
    var body = document.body;
    if (!frameRoot || !frameRoot.style || !body || typeof body.getBoundingClientRect !== "function") { return; }
    var gutter = Math.max(0, Math.round((window.innerWidth || 0) - body.getBoundingClientRect().width));
    heldGutter = gutter;
    var value = gutter + "px";
    if (frameRoot.style.getPropertyValue("--gutter") !== value) { frameRoot.style.setProperty("--gutter", value); }
  }

  /** Clip the frame's overflow until every height has stopped moving and the frame has
      caught up with it. */
  function settleFrame() {
    if (!frameRoot) { return; }
    frameRoot.setAttribute("data-settling", "1");
    settleStill = 0;
    if (settleQueued) { return; }
    if (typeof window.requestAnimationFrame !== "function") { frameRoot.removeAttribute("data-settling"); return; }
    settleQueued = true;
    window.requestAnimationFrame(watchSettle);
  }

  function watchSettle() {
    settleQueued = false;
    var viewport = frameRoot.clientHeight || 0;
    var moving = heightShell.getAttribute("data-moving") === "1" || regionMoving();
    settleStill = moving || viewport !== settleViewport ? 0 : settleStill + 1;
    settleViewport = viewport;
    var fits = (frameRoot.scrollHeight || 0) <= viewport;
    if (!moving && settleStill >= 1 && (fits || settleStill >= SETTLE_FRAMES)) {
      frameRoot.removeAttribute("data-settling");
      return;
    }
    settleQueued = true;
    window.requestAnimationFrame(watchSettle);
  }

  function followHeight() {
    holdGutter();
    // The fallback line drawn while nothing has been delivered is not the card's height.
    if (!payload()) { return; }
    var target = heightContent.offsetHeight || 0;
    if (target <= 0 || target === shownHeight) { return; }
    var from = shownHeight;
    shownHeight = target;
    settleFrame();
    var moving = heightShell.getAttribute("data-moving") === "1";
    if (from === null || reducedMotion() || (!moving && regionMoving())) {
      if (moving) { settleHeight(); }
      return;
    }
    if (!moving) {
      // Pin the height the card was showing and commit it, so the change below is a move
      // between two lengths rather than a jump from auto.
      heightShell.setAttribute("data-moving", "1");
      heightShell.style.height = from + "px";
      void heightShell.offsetHeight;
    }
    // Mid-move, a new length retargets the running transition from wherever it has got to.
    heightShell.style.height = target + "px";
  }

  // Before the first card is drawn, so the first height it lands at is already laid out
  // with the gutter given back.
  holdGutter();

  if (heightShell && heightContent) {
    var arrived = function (event) {
      if (event.target === heightShell && event.propertyName === "height" && !shellStillMoving()) { settleHeight(); }
    };
    heightShell.addEventListener("transitionend", arrived);
    heightShell.addEventListener("transitioncancel", arrived);
    // A region that eases its own size moves the card without the shell: clip for it too.
    document.addEventListener("transitionrun", function (event) {
      if (SIZE_PROPERTY.test(event.propertyName || "")) { settleFrame(); }
    }, true);
    if (typeof window.ResizeObserver === "function") {
      new window.ResizeObserver(followHeight).observe(heightContent);
    }
  }

  var initId = rpc("ui/initialize", {
    appInfo: { name: "AI Producer choices", version: "9" },
    appCapabilities: {},
    protocolVersion: "2026-01-26"
  });
  pending[initId] = function (ok, result) {
    initialized = ok;
    var caps = (ok && result && result.hostCapabilities) || {};
    canMessage = !!caps.message;
    // The picker needs a host that relays a card's tools/call; the image block needs one
    // that says its messages carry images. Anything less falls back to the intent tile.
    canCallTools = !!caps.serverTools;
    canSendImage = !!(caps.message && caps.message.image);
    if (canCallTools && imageGroupOf(shown)) { render(); }
    // The ceiling the host will crop this frame at. Recorded, not yet acted on: a card
    // taller than it scrolls inside the frame, and nothing here can raise it.
    var box = result && result.hostContext && result.hostContext.containerDimensions;
    if (box && typeof box.maxHeight === "number" && document.body) {
      document.body.setAttribute("data-max-height", String(box.maxHeight));
    }
    if (ok) {
      window.parent.postMessage({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} }, "*");
      resendSize();
    }
  };
  render();
})();

  }

  window.AIPDecisionCard = {
    version: "29",
    render: function (output, options) {
      if (mounted) { throw new Error("AIPDecisionCard renders one card per widget"); }
      mounted = true;
      var style = document.createElement("style");
      style.textContent = STYLE;
      document.head.appendChild(style);
      var holder = document.createElement("div");
      holder.innerHTML = SHELL;
      var target = options && options.mount ? document.getElementById(options.mount) : null;
      (target || document.body).appendChild(holder.firstElementChild);
      var data = localize(output);
      // A caller's key keeps the sent state across a remount, as the service's view id does.
      if (options && typeof options.key === "string" && options.key) {
        data._meta = Object.assign({}, data._meta, { viewUUID: options.key });
      }
      window.openai = {
        toolOutput: data,
        sendFollowUpMessage: function (args) { return send(args && args.prompt); }
      };
      runCard();
    }
  };
})();

"""Exercise bounded host batches with synthetic tools, receipts, and uploads."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts/publication_batch.js"
HARNESS = r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
const create = eval(fs.readFileSync(process.argv[2], 'utf8'));
const tick = () => new Promise(resolve => setImmediate(resolve));
function argv(command) {
  const source = command.split(" <<'AIP_UPLOAD_JSON'\n")[0];
  const values = []; let word = '', quoted = false, started = false;
  for (let index = 0; index < source.length; index++) {
    const char = source[index];
    if (char === "'") { quoted = !quoted; started = true; }
    else if (!quoted && char === '\\') { word += source[++index]; started = true; }
    else if (!quoted && /\s/.test(char)) {
      if (started) { values.push(word); word = ''; started = false; }
    } else { word += char; started = true; }
  }
  assert.equal(quoted, false);
  if (started) values.push(word);
  return values;
}
const option = (args, name) => args.includes(name) ? args[args.indexOf(name) + 1] : undefined;
const options = (args, name) => args.flatMap((value, index) => value === name ? [args[index + 1]] : []);
function fixture(config = {}) {
  const commands = [], events = [], commits = [], failures = [], joins = [], warnings = new Set();
  const delays = [], markers = [], waitCalls = [];
  let published = 0, pending, failed = false, yielded = 0, polls = 0, envelope = 0;
  let elapsed = 0;
  const waiting = new Set();
  const yieldWaiting = new Set();
  const notify = () => { for (const resolve of waiting) resolve(); waiting.clear(); };
  const response = value => ({exit_code: 0, output: JSON.stringify(value)});
  const wrap = value => ++envelope % 2
    ? {structuredContent: value, content: [{type: 'text', text: 'not the receipt'}]}
    : {content: [{type: 'text', text: 'service note'}, {type: 'text', text: JSON.stringify(value)}]};
  const isFailure = (phase, effect) => config.failPhase === phase && config.failEffect === effect;
  const error = () => { throw new Error('https://secret.invalid/?credential=PRIVATE_SENTINEL'); };
  const tools = {
    async exec_command({cmd}) {
      commands.push(cmd);
      const args = argv(cmd);
      if (args[1].endsWith('/upload_batch.py')) {
        const targets = JSON.parse(cmd.split(" <<'AIP_UPLOAD_JSON'\n")[1].split('\nAIP_UPLOAD_JSON')[0]);
        assert.deepEqual(targets.map(row => row.path), pending.plan.expected_files.map(row => row.path));
        events.push(['upload', pending.effect]);
        if (isFailure('upload', pending.effect)) error();
        pending.uploaded = true;
        return {session_id: 71, output: '{"ok":'};
      }
      const operation = args[2];
      if (operation === 'prepare') {
        const previous = Number(option(args, '--after-effect') || 0);
        const effect = previous + 1;
        joins.push({effect, after: option(args, '--after-effect'), batch: args.includes('--batch-join')});
        if (previous - published > (args.includes('--batch-join') ? 2 : 1)) error();
        while (published !== previous || pending) {
          if (failed || published > previous) error();
          await new Promise(resolve => waiting.add(resolve));
        }
        if (failed) error();
        if (isFailure('prepare', effect)) error();
        const files = options(args, '--file');
        const supplied = options(args, '--upload-file');
        const final = args.includes('--final');
        const expected_files = files.map(path => ({path: 'render-engine/' + path, sha256: String(effect).padStart(64, '0')}));
        const plan = {status: 'prepared', project_id: 'synthetic-project', base_digest: `digest-${previous}`,
          sign_batches: expected_files.map(row => [{path: row.path, content_type: 'text/html'}]),
          expected_files, authoring: !final, final, published_effects: effect, duration_seconds: 59.85,
          ...(supplied.length ? {asset_origins: supplied.map(path =>
            ({path: 'render-engine/' + path, origin: 'upload'}))} : {})};
        pending = {effect, plan, waits: 0, uploaded: false};
        events.push(['prepare', effect]);
        return response(isFailure('plan-count', effect) ? {...plan, published_effects: effect + 1} : plan);
      }
      if (operation === 'accept') {
        const effect = pending.effect;
        if (isFailure('accept', effect)) error();
        assert.equal(option(args, '--task-id'), `task-${effect}`);
        assert.equal(option(args, '--digest'), `digest-${effect}`);
        assert.deepEqual(options(args, '--accepted-file'), pending.plan.expected_files.map(row => row.path));
        for (const code of options(args, '--warning-code')) warnings.add(code);
        const final = pending.plan.final;
        published = effect; pending = undefined;
        events.push(['accept', effect]); notify();
        return response({published_effects: isFailure('receipt-count', effect) ? effect + 1 : effect,
          final, task_id: `task-${effect}`, duration_seconds: 59.85, warning_codes: [...warnings].sort(),
          ignored_service_url: 'https://secret.invalid/PRIVATE_SENTINEL'});
      }
      assert.equal(operation, 'fail');
      const effect = Number(option(args, '--effect'));
      failures.push(effect);
      if (config.failMarker) error();
      failed = true; pending = undefined; notify();
      return response({status: 'failed', published_effects: published});
    },
    async write_stdin(args) {
      assert.equal(args.session_id, 71); assert.equal(args.chars, '');
      polls++;
      return polls % 2 ? {session_id: 71, output: 'true,'} : {exit_code: 0, output: '"files":[]}'};
    },
  };
  const runBatch = create({tools, skill: config.skill || '/skill', workspace: config.workspace || '/render-engine',
    now: () => elapsed, delay: async ms => { delays.push(ms); elapsed += ms; },
    onReady: marker => {
      if (config.onReadyError) error();
      markers.push(marker); events.push(['ready', marker.through_effect]);
    },
    state: config.state || '/state.json', yieldControl: async () => {
      yielded++; events.push(['yield']);
      for (const resolve of yieldWaiting) resolve(); yieldWaiting.clear();
    },
    signUpload: async args => {
      assert.equal(args.authoring, true);
      events.push(['sign', pending.effect]);
      if (isFailure('sign', pending.effect)) error();
      if (isFailure('tool-error', pending.effect)) return {isError: true,
        content: [{type: 'text', text: 'https://secret.invalid/PRIVATE_SENTINEL'}]};
      if (isFailure('sign-count', pending.effect)) return wrap({uploads: [], rejected: []});
      return wrap({uploads: args.files.map(file => ({path: file.path,
        upload_url: "https://uploads.example.invalid/u?token='$(touch upload-marker)`touch upload-marker2`",
        headers: {'x-test': 'PRIVATE_SENTINEL'}})), rejected: []});
    },
    commitWorkspace: async args => {
      const effect = pending.effect;
      assert.equal(pending.uploaded, true);
      assert.equal(args.base_digest, `digest-${effect - 1}`);
      assert.equal(args.authoring, pending.plan.authoring);
      assert.deepEqual(args.expected_files, pending.plan.expected_files);
      assert.deepEqual(args.asset_origins, pending.plan.asset_origins);
      commits.push(args); events.push(['commit', effect]);
      if (isFailure('commit', effect)) error();
      return wrap({task_id: `task-${effect}`, page_url: 'https://secret.invalid/PRIVATE_SENTINEL'});
    },
    waitTask: async args => {
      const effect = pending.effect;
      assert.equal(args.task_id, `task-${effect}`);
      assert.ok(args.wait_seconds > 0 && args.wait_seconds <= 45);
      waitCalls.push(args);
      elapsed += config.clockAdvancePerWait || 0;
      events.push(['wait', effect]);
      await tick();
      if (config.hold) await config.hold;
      if (config.waitReplies?.length) return wrap(config.waitReplies.shift());
      if (config.repeatWait) return wrap(config.repeatWait);
      if (isFailure('wait', effect)) error();
      if (isFailure('task-status', effect)) return wrap({});
      if (isFailure('hold-limit', effect)) return wrap({status: 'running', wait: {woke_on: 'hold_limit'}});
      if (pending.waits++ === 0) return wrap({status: 'running', wait: {woke_on: 'timeout'}});
      return wrap({status: 'done', succeeded: !isFailure('refused', effect), result: {
        outcome: isFailure('refused', effect) ? 'refused' : 'accepted_with_warnings',
        accepted: pending.plan.expected_files.map((row, index) => index % 2 ? row.path : {path: row.path}),
        workspace_digest: `digest-${effect}`,
        warnings: effect === 1 ? [{rule: 'runtime_check_unavailable'}] : [],
      }});
    },
  });
  return {runBatch, commands, events, commits, failures, joins, delays, markers, waitCalls,
    async waitForYields(count) {
      while (yielded < count) await new Promise(resolve => yieldWaiting.add(resolve));
    },
    get yielded() { return yielded; }, get polls() { return polls; }};
}
const step = number => ({draft: `/draft-${number}`, files: ['index.html', `compositions/effect-${number}.html`]});
'''


@unittest.skipUnless(shutil.which("node"), "Node is needed only for host-JavaScript tests")
class PublicationBatchTests(unittest.TestCase):
    def run_node(self, body, arguments=()):
        result = subprocess.run(
            ["node", "--input-type=module", "-", str(SCRIPT), *arguments], input=HARNESS + body,
            text=True, capture_output=True, timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_eight_and_nine_effects_publish_in_order_with_one_yield_per_batch(self):
        self.run_node(r'''
for (const count of [8, 9]) {
  const harness = fixture();
  const jobs = [];
  for (let after = 0; after < count;) {
    const size = after === 0 ? 1 : Math.min(2, count - after);
    jobs.push(harness.runBatch({afterEffect: after,
      steps: Array.from({length: size}, (_, index) => step(after + index + 1)), final: after + size === count}));
    after += size;
    if (after < count) await harness.waitForYields(jobs.length);
  }
  const summaries = await Promise.all(jobs);
  assert.equal(harness.yielded, jobs.length - 1);
  assert.equal(harness.yielded, 4);
  assert.deepEqual(harness.markers, [1, 3, 5, 7].map(through_effect => ({status: 'batch_publishing', through_effect})));
  assert.ok(harness.waitCalls.every(args => args.wait_seconds === 45));
  assert.equal(harness.polls, count * 2, 'every upload session must be completely drained');
  assert.deepEqual(harness.events.filter(row => row[0] === 'accept').map(row => row[1]),
    Array.from({length: count}, (_, index) => index + 1));
  assert.deepEqual(harness.commits.map(row => row.base_digest),
    Array.from({length: count}, (_, index) => `digest-${index}`));
  assert.deepEqual(harness.commits.map(row => row.authoring), Array(count - 1).fill(true).concat(false));
  assert.equal(harness.joins.find(row => row.effect === 1).after, undefined);
  for (const row of harness.joins.filter(row => row.effect > 1)) {
    assert.equal(row.after, String(row.effect - 1));
    assert.equal(row.batch, row.effect % 2 === 0);
  }
  assert.equal(summaries.at(-1).published_effects, count);
  assert.equal(summaries.at(-1).final, true);
  assert.deepEqual(summaries.at(-1).warning_codes, ['runtime_check_unavailable']);
  assert.equal(JSON.stringify(summaries).includes('PRIVATE_SENTINEL'), false);
  assert.equal(JSON.stringify(summaries).includes('https://'), false);
}
''')

    def test_user_supplied_files_are_declared_on_the_commit_that_stages_them(self):
        self.run_node(r'''
const harness = fixture();
const staged = {draft: '/draft-1', uploads: ['public/images/user-photo.jpg'],
  files: ['index.html', 'compositions/effect-1.html', 'public/images/user-photo.jpg']};
await harness.runBatch({afterEffect: 0, steps: [staged], final: true});
const prepared = argv(harness.commands.find(cmd => argv(cmd)[2] === 'prepare'));
assert.deepEqual(options(prepared, '--upload-file'), ['public/images/user-photo.jpg']);
assert.deepEqual(harness.commits[0].asset_origins,
  [{path: 'render-engine/public/images/user-photo.jpg', origin: 'upload'}]);
await assert.rejects(harness.runBatch({afterEffect: 1, final: true,
  steps: [{...staged, uploads: ['public/images/never-staged.jpg']}]}), /invalid_publication_batch/);
assert.equal(harness.commits.length, 1, 'an undeclarable origin stops the batch before any commit');
''')

    def test_a_batch_without_supplied_files_commits_no_origins(self):
        self.run_node(r'''
const harness = fixture();
await harness.runBatch({afterEffect: 0, steps: [step(1)], final: true});
assert.equal('asset_origins' in harness.commits[0], false);
''')

    def test_yield_keeps_publication_awaited_until_its_receipt(self):
        self.run_node(r'''
let release;
const harness = fixture({hold: new Promise(resolve => { release = resolve; })});
let settled = false;
const job = harness.runBatch({afterEffect: 0, steps: [step(1)], final: false})
  .then(value => { settled = true; return value; });
await tick();
assert.equal(harness.yielded, 1);
assert.equal(settled, false);
release();
assert.equal((await job).published_effects, 1);
await harness.runBatch({afterEffect: 1, steps: [step(2), step(3)], final: true});
assert.equal(harness.yielded, 1, 'final batch must never yield');
''')

    def test_slow_previous_batch_blocks_a_second_speculative_continuation(self):
        self.run_node(r'''
let release;
const harness = fixture({hold: new Promise(resolve => { release = resolve; })});
const first = harness.runBatch({afterEffect: 0, steps: [step(1)], final: false});
await harness.waitForYields(1);
const second = harness.runBatch({afterEffect: 1, steps: [step(2), step(3)], final: false});
await tick(); await tick();
assert.equal(harness.yielded, 1, 'fast drafting must not yield again while the preceding publication is pending');
assert.deepEqual(harness.markers, [{status: 'batch_publishing', through_effect: 1}]);
assert.equal(harness.events.some(row => row[0] === 'prepare' && row[1] === 2), false);
release();
await harness.waitForYields(2);
const acceptedFirst = harness.events.findIndex(row => row[0] === 'accept' && row[1] === 1);
const preparedSecond = harness.events.findIndex(row => row[0] === 'prepare' && row[1] === 2);
assert.ok(acceptedFirst >= 0 && preparedSecond > acceptedFirst);
const final = harness.runBatch({afterEffect: 3, steps: [step(4)], final: true});
const summaries = await Promise.all([first, second, final]);
assert.equal(summaries.at(-1).published_effects, 4);
assert.deepEqual(harness.failures, []);
assert.equal(harness.yielded, 2);
assert.deepEqual(harness.markers, [1, 3].map(through_effect => ({status: 'batch_publishing', through_effect})));
''')

    def test_interrupted_holds_wait_and_resume_the_same_task_without_recommitting(self):
        self.run_node(r'''
const harness = fixture({waitReplies: [
  {task_id: 'task-1', status: 'running', terminal: false, wait: {woke_on: 'hold_limit'},
   poll_after_seconds: 15, next_data: {poll_args: {task_id: 'task-1', wait_seconds: 45}}},
  {task_id: 'task-1', status: 'running', terminal: false, wait: {woke_on: 'superseded'},
   next_data: {poll_after_seconds: 7, poll_args: {task_id: 'task-1', wait_seconds: 45}}},
]});
const summary = await harness.runBatch({afterEffect: 0, steps: [step(1)], final: true});
assert.equal(summary.published_effects, 1);
assert.deepEqual(harness.delays, [15000, 7000]);
assert.equal(harness.commits.length, 1);
assert.ok(harness.waitCalls.every(args => args.task_id === 'task-1' && args.wait_seconds === 45));
assert.deepEqual(harness.failures, []);
assert.deepEqual(harness.markers, []);
''')

    def test_malformed_or_unbounded_waits_fail_safely_without_repeated_mutations(self):
        self.run_node(r'''
const malformed = [
  {status: 'unknown'}, {status: 'running', task_id: 'other-task'},
  {status: 'running', terminal: true}, {status: 'done', terminal: false},
  {status: 'running', next_data: {poll_args: {task_id: 'other-task', wait_seconds: 45}}},
  {status: 'running', next_data: {poll_args: {task_id: 'task-1', wait_seconds: 900}}},
  {status: 'running', wait: {woke_on: 'hold_limit'}, poll_after_seconds: -1},
];
for (const reply of malformed) {
  const harness = fixture({waitReplies: [reply]});
  await assert.rejects(harness.runBatch({afterEffect: 0, steps: [step(1)], final: true}),
    error => error.message === 'publication_not_accepted');
  assert.equal(harness.waitCalls.length, 1);
  assert.equal(harness.commits.length, 1);
  assert.deepEqual(harness.failures, [1]);
}
for (const clockAdvancePerWait of [0, 400000]) {
  const harness = fixture({repeatWait: {status: 'running', terminal: false}, clockAdvancePerWait});
  await assert.rejects(harness.runBatch({afterEffect: 0, steps: [step(1)], final: true}), /publication_not_accepted/);
  assert.equal(harness.waitCalls.length, clockAdvancePerWait ? 2 : 40);
  assert.equal(harness.commits.length, 1);
  assert.deepEqual(harness.failures, [1]);
}
const callback = fixture({onReadyError: true});
await assert.rejects(callback.runBatch({afterEffect: 0, steps: [step(1)], final: false}),
  error => error.message === 'publication_yield_failed');
assert.equal(callback.yielded, 0);
assert.deepEqual(callback.events.filter(row => row[0] === 'accept'), [['accept', 1]], 'callback error must still drain the job');
''')

    def test_claimed_and_stalled_timeouts_continue_waiting_for_the_same_commit(self):
        self.run_node(r'''
const harness = fixture({waitReplies: [
  ...['claimed', 'stalled'].map(status => ({task_id: 'task-1', status, terminal: false,
    wait: {woke_on: 'timeout'}, poll_after_seconds: 0,
    next_data: {poll_args: {task_id: 'task-1', wait_seconds: 45}}})),
  {task_id: 'task-1', status: 'done', terminal: true, succeeded: true, result: {
    outcome: 'accepted', accepted: ['render-engine/index.html', 'render-engine/compositions/effect-1.html'],
    digest: 'digest-1', warnings: [],
  }},
]});
const summary = await harness.runBatch({afterEffect: 0, steps: [step(1)], final: true});
assert.equal(summary.published_effects, 1);
assert.equal(summary.final, true);
assert.equal(harness.commits.length, 1);
assert.equal(harness.waitCalls.length, 3);
assert.ok(harness.waitCalls.every(args => args.task_id === 'task-1' && args.wait_seconds === 45));
assert.deepEqual(harness.failures, []);
''')

    def test_failures_stop_before_later_effect_and_hide_raw_tool_details(self):
        self.run_node(r'''
for (const failPhase of ['prepare', 'sign', 'tool-error', 'sign-count', 'upload', 'commit', 'wait',
                        'task-status', 'hold-limit', 'refused', 'accept', 'plan-count', 'receipt-count']) {
  const harness = fixture({failPhase, failEffect: 2});
  await harness.runBatch({afterEffect: 0, steps: [step(1)], final: false});
  await assert.rejects(harness.runBatch({afterEffect: 1, steps: [step(2), step(3)], final: true}),
    error => error.message === 'publication_not_accepted');
  assert.deepEqual(harness.failures, [2]);
  assert.equal(harness.events.some(row => row[1] === 3), false, failPhase);
}
const unavailable = fixture({failPhase: 'sign', failEffect: 1, failMarker: true});
await assert.rejects(unavailable.runBatch({afterEffect: 0, steps: [step(1)], final: true}),
  error => error.message === 'publication_failed_checkpoint_unavailable');
const unprepared = fixture({failPhase: 'prepare', failEffect: 1});
await assert.rejects(unprepared.runBatch({afterEffect: 0, steps: [step(1)], final: false}),
  error => error.message === 'publication_not_accepted');
assert.equal(unprepared.yielded, 0, 'a failed first prepare must not release another authoring continuation');
assert.deepEqual(unprepared.failures, [1]);
''')

    def test_invalid_batch_and_step_specs_are_refused_before_any_tools_or_yield(self):
        self.run_node(r'''
const cases = [
  {afterEffect: 0, steps: [step(1), step(2)], final: false},
  {afterEffect: 1, steps: [step(2), step(3), step(4)], final: true},
  {afterEffect: -1, steps: [step(1)], final: false},
  {afterEffect: 0.5, steps: [step(1)], final: false},
  {afterEffect: true, steps: [step(1)], final: false},
  {afterEffect: 0, steps: [], final: false},
  {afterEffect: 0, steps: [step(1)]},
  {afterEffect: 1, steps: [step(2), {draft: 'relative', files: ['index.html']}], final: true},
  {afterEffect: 1, steps: [step(2), {draft: '/draft', files: ['index.html', '../escape']}], final: true},
  {afterEffect: 0, steps: [{draft: '/draft', files: ['index.html', 'index.html']}], final: true},
];
for (const spec of cases) {
  const harness = fixture();
  await assert.rejects(harness.runBatch(spec), /invalid_publication_batch/);
  assert.deepEqual(harness.commands, []); assert.deepEqual(harness.events, []);
}
''')

    def test_shell_quoting_preserves_paths_and_signed_stdin_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            special = "quote' $(touch path-marker) `touch path-marker2`"
            skill = base / special
            scripts = skill / "scripts"
            scripts.mkdir(parents=True)
            checkpoint = scripts / "progressive_checkpoint.py"
            checkpoint.write_text("import json,sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
            uploader = scripts / "upload_batch.py"
            uploader.write_text(
                "import json,sys\nprint(json.dumps({'argv':sys.argv[1:],'stdin':json.load(sys.stdin)}))\n",
                encoding="utf-8",
            )
            config = {"skill": str(skill), "workspace": str(base / (special + " workspace")),
                      "state": str(base / (special + " state"))}
            commands = json.loads(self.run_node(r'''
const config = JSON.parse(process.argv[3]);
const harness = fixture(config);
await harness.runBatch({afterEffect: 0, steps: [{draft: config.workspace + " draft'",
  files: ['index.html', "compositions/quote' $(touch file-marker).html"]}], final: true});
console.log(JSON.stringify(harness.commands));
''', [json.dumps(config)]))
            decoded = []
            for command in commands:
                result = subprocess.run(command, shell=True, cwd=base, text=True, capture_output=True,
                                        timeout=5, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                decoded.append(json.loads(result.stdout))
            self.assertEqual(decoded[0][decoded[0].index("--workspace") + 1], config["workspace"])
            self.assertEqual(decoded[0][decoded[0].index("--draft") + 1], config["workspace"] + " draft'")
            self.assertIn("compositions/quote' $(touch file-marker).html", decoded[0])
            self.assertEqual(decoded[1]["argv"], [config["workspace"]])
            self.assertIn("$(touch upload-marker)", decoded[1]["stdin"][0]["upload_url"])
            self.assertEqual(sorted(path.name for path in base.iterdir()), [special])


if __name__ == "__main__":
    unittest.main()

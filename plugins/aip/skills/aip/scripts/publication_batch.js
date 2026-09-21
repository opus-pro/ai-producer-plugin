/* Publish bounded batches in the current host while the next batch is authored. */
(function publicationBatch({ tools, yieldControl, skill, workspace, state, signUpload, commitWorkspace, waitTask,
  onReady = () => {}, delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms)), now = () => Date.now() }) {
  const WAIT_SECONDS = 45;
  const MAX_WAIT_MILLISECONDS = 600000;
  const MAX_WAIT_ATTEMPTS = 40;
  const INTERRUPTED_HOLD_DELAY_SECONDS = 15;
  const absolute = (value) => typeof value === "string" && value.startsWith("/") && !value.includes("\0");
  if (![skill, workspace, state].every(absolute) || !tools ||
      ![tools.exec_command, tools.write_stdin, yieldControl, signUpload, commitWorkspace, waitTask, onReady, delay, now]
        .every((value) => typeof value === "function")) throw new Error("invalid_publication_adapter");
  const quote = (value) => "'" + String(value).replace(/'/g, "'\\''") + "'";
  const checkpoint = ["python3", skill + "/scripts/progressive_checkpoint.py"];
  const scope = ["--workspace", workspace, "--state", state];
  const shell = (args) => args.map(quote).join(" ");
  const object = (value) => value && typeof value === "object" && !Array.isArray(value);

  function unpack(response) {
    if (!object(response) || response.isError) throw new Error("publication_tool_failed");
    if (object(response.structuredContent)) return response.structuredContent;
    for (const block of response.content || []) {
      if (block.type !== "text") continue;
      try {
        const value = JSON.parse(block.text);
        if (object(value)) return value;
      } catch { /* Other text blocks are not a machine-readable receipt. */ }
    }
    throw new Error("publication_tool_receipt_missing");
  }

  async function command(cmd) {
    let response = await tools.exec_command({ cmd, yield_time_ms: 1000, max_output_tokens: 20000 });
    let output = response.output || "";
    while (response.session_id !== undefined && response.session_id !== null) {
      response = await tools.write_stdin({
        session_id: response.session_id, chars: "", yield_time_ms: 1000, max_output_tokens: 20000,
      });
      output += response.output || "";
    }
    if (response.exit_code !== 0) throw new Error("publication_local_command_failed");
    const value = JSON.parse(output);
    if (!object(value)) throw new Error("publication_local_receipt_missing");
    return value;
  }

  function batchSpec(spec) {
    const { afterEffect, steps, final } = spec || {};
    if (!Number.isSafeInteger(afterEffect) || afterEffect < 0 || typeof final !== "boolean" ||
        !Array.isArray(steps) || steps.length < 1 || steps.length > (afterEffect === 0 ? 1 : 2) ||
        !Number.isSafeInteger(afterEffect + steps.length)) throw new Error("invalid_publication_batch");
    return { afterEffect, final, steps: steps.map((step) => {
      const uploads = step?.uploads ?? [];
      if (!object(step) || !absolute(step.draft) || !Array.isArray(step.files) ||
          !step.files.includes("index.html") || new Set(step.files).size !== step.files.length ||
          !step.files.every((path) => typeof path === "string" && path.length > 0 &&
            !path.startsWith("/") && !path.startsWith("-") && !path.includes("\0") &&
            path.split("/").every((part) => part && part !== "." && part !== "..")) ||
          // A user-supplied file is one of this step's own files; anything else
          // would declare an origin for bytes this commit never stages.
          !Array.isArray(uploads) || new Set(uploads).size !== uploads.length ||
          !uploads.every((path) => step.files.includes(path))) {
        throw new Error("invalid_publication_batch");
      }
      return { draft: step.draft, files: step.files.slice(), uploads: uploads.slice() };
    }) };
  }

  async function waitForReceipt(taskId) {
    const deadline = now() + MAX_WAIT_MILLISECONDS;
    let holdSeconds = WAIT_SECONDS;
    for (let attempt = 0; attempt < MAX_WAIT_ATTEMPTS; attempt++) {
      if (now() >= deadline) throw new Error("publication_wait_timeout");
      const task = unpack(await waitTask({ task_id: taskId,
        wait_seconds: Math.min(holdSeconds, Math.max(1, Math.ceil((deadline - now()) / 1000))) }));
      const terminal = ["done", "failed", "cancelled"].includes(task.status);
      if (!["queued", "claimed", "running", "stalled", "awaiting_input", "deferred", "done", "failed", "cancelled"]
          .includes(task.status) ||
          (task.task_id !== undefined && task.task_id !== taskId) ||
          (task.terminal !== undefined && task.terminal !== terminal)) throw new Error("publication_task_malformed");
      if (now() >= deadline) throw new Error("publication_wait_timeout");
      if (terminal) return task;
      const poll = task.next_data?.poll_args;
      if (poll !== undefined) {
        if (!object(poll) || poll.task_id !== taskId || !Number.isInteger(poll.wait_seconds) ||
            poll.wait_seconds < 1 || poll.wait_seconds > WAIT_SECONDS) throw new Error("publication_task_malformed");
        holdSeconds = poll.wait_seconds;
      }
      if (["hold_limit", "superseded"].includes(task.wait?.woke_on)) {
        const seconds = task.poll_after_seconds ?? task.next_data?.poll_after_seconds ?? INTERRUPTED_HOLD_DELAY_SECONDS;
        if (!Number.isFinite(seconds) || seconds < 0) throw new Error("publication_task_malformed");
        let milliseconds = seconds * 1000;
        if (milliseconds >= deadline - now()) throw new Error("publication_wait_timeout");
        while (milliseconds > 0) {
          const pause = Math.min(milliseconds, 60000);
          await delay(pause);
          milliseconds -= pause;
        }
      }
    }
    throw new Error("publication_wait_timeout");
  }

  async function publish(step, previous, final, joinBatch, prepared) {
    const args = [...checkpoint, "prepare", ...scope, "--draft", step.draft];
    if (previous > 0) args.push("--after-effect", previous, ...(joinBatch ? ["--batch-join"] : []));
    for (const file of step.files) args.push("--file", file);
    for (const file of step.uploads) args.push("--upload-file", file);
    if (final) args.push("--final");
    const plan = await command(shell(args));
    if (plan.status !== "prepared" || plan.published_effects !== previous + 1 ||
        plan.final !== final || plan.authoring !== !final || !Array.isArray(plan.sign_batches) ||
        !plan.sign_batches.length || !Array.isArray(plan.expected_files) || !plan.expected_files.length) {
      throw new Error("publication_plan_mismatch");
    }
    if (prepared) prepared();
    const targets = [];
    for (const files of plan.sign_batches) {
      const signed = unpack(await signUpload({ project_id: plan.project_id, authoring: true, files }));
      if (signed.rejected?.length || !Array.isArray(signed.uploads) || signed.uploads.length !== files.length ||
          new Set(signed.uploads.map((row) => row.path)).size !== files.length ||
          signed.uploads.some((row) => !files.some((file) => file.path === row.path))) {
        throw new Error("publication_signing_refused");
      }
      targets.push(...signed.uploads);
    }
    // A quoted heredoc supplies signed targets only to the uploader's stdin.
    const upload = await command(shell(["python3", skill + "/scripts/upload_batch.py", workspace]) +
      " <<'AIP_UPLOAD_JSON'\n" + JSON.stringify(targets) + "\nAIP_UPLOAD_JSON");
    if (upload.ok !== true) throw new Error("publication_upload_failed");
    const committed = unpack(await commitWorkspace({
      project_id: plan.project_id, base_digest: plan.base_digest,
      expected_files: plan.expected_files, authoring: plan.authoring,
      // A plan from a helper the service predates carries no origins; the
      // commit then leaves every staged media file at the service default.
      ...(Array.isArray(plan.asset_origins) && plan.asset_origins.length
        ? { asset_origins: plan.asset_origins } : {}),
    }));
    if (typeof committed.task_id !== "string" || !committed.task_id) throw new Error("publication_task_missing");
    const task = await waitForReceipt(committed.task_id);
    const receipt = task.result;
    if (task.succeeded !== true || !["accepted", "accepted_with_warnings"].includes(receipt?.outcome) ||
        !Array.isArray(receipt.accepted)) throw new Error("publication_not_accepted");
    const digest = receipt.digest || receipt.workspace_digest;
    if (typeof digest !== "string" || !digest) throw new Error("publication_digest_missing");
    const accepted = [...checkpoint, "accept", ...scope, "--task-id", committed.task_id, "--digest", digest];
    for (const row of receipt.accepted) {
      const path = typeof row === "string" ? row : row?.path;
      if (typeof path !== "string" || !path || path.includes("\0")) throw new Error("publication_receipt_mismatch");
      accepted.push("--accepted-file", path);
    }
    for (const warning of receipt.warnings || []) {
      const code = warning.rule || warning.code;
      if (typeof code === "string" && /^[a-zA-Z0-9_-]{1,100}$/.test(code)) accepted.push("--warning-code", code);
    }
    const summary = await command(shell(accepted));
    if (summary.published_effects !== previous + 1 || summary.final !== final ||
        summary.task_id !== committed.task_id || !Array.isArray(summary.warning_codes)) {
      throw new Error("publication_receipt_mismatch");
    }
    return { published_effects: summary.published_effects, duration_seconds: summary.duration_seconds,
      task_id: summary.task_id, final: summary.final, warning_codes: summary.warning_codes };
  }

  return async function runBatch(spec) {
    const { afterEffect, steps, final } = batchSpec(spec);
    let effect = afterEffect + 1;
    let resolvePrepared;
    const firstPrepared = new Promise((resolve) => { resolvePrepared = resolve; });
    // Capture every rejection before yielding, and drain the whole job in this cell.
    const job = (async () => {
      try {
        let receipt;
        for (let index = 0; index < steps.length; index++) {
          effect = afterEffect + index + 1;
          receipt = await publish(steps[index], effect - 1, final && index === steps.length - 1,
            index === 0, index === 0 ? () => resolvePrepared(true) : null);
        }
        return { accepted: true, receipt };
      } catch {
        resolvePrepared(false);
        try {
          await command(shell([...checkpoint, "fail", ...scope, "--effect", effect]));
          return { accepted: false, error: "publication_not_accepted" };
        } catch {
          return { accepted: false, error: "publication_failed_checkpoint_unavailable" };
        }
      }
    })();
    // Join the preceding batch before releasing another authoring continuation.
    if (!final && await firstPrepared) {
      try {
        await onReady({ status: "batch_publishing", through_effect: afterEffect + steps.length });
        await yieldControl();
      }
      catch { await job; throw new Error("publication_yield_failed"); }
    }
    const result = await job;
    if (!result.accepted) throw new Error(result.error);
    return result.receipt;
  };
})

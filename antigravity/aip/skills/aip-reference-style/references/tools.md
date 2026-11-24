# A reference on this computer

What getting and reading a reference and matching its captions need on this machine, for the [reference style skill](../SKILL.md).

## Tools

What reading the reference and matching its captions need on the machine, ffmpeg, python3 and uv, you set up yourself without asking the user: install what is missing. A missing tool is never a reason to stop or to edit without the reference, except on a host whose own instructions say you cannot install anything: there they win, and you stop as they say.

## Downloads

- A link: download the `start_link_download` answer's `download_url` before `download_expires_at` into a new directory in the project's working folder, outside its `render-engine/`, saved under the answer's `file_name`.
- A preset: download the `get_reference_preset` answer's `folder.download_url` before `download_expires_at` and unpack it into a new directory in the project's working folder, outside its `render-engine/`.
- A file sent from the AI Producer web page: download each `download_url` before its link expires.

A link that expired is fetched again with the same call.

## Files

Never delete with a shell wildcard, such as `rm -f out/*` or `rm frames/*.png`: Claude Code stops for the user's approval on every such delete, whatever its permission mode, and refuses it where no one can answer. To redo a set of files, write the new set into a new directory and use that one, or overwrite each file by its name; a script of yours that replaces its own output deletes only the files it wrote, by name, from inside the script.

## Caption pages

The caption pages render locally with a headless browser; one the host's sandbox stops from starting usually starts with Chrome's `--single-process`.

## The caption match in a subagent

A reference without a pack has its captions matched against the kit, as the skill's [Matching the captions](../SKILL.md#matching-the-captions) says. Only in Claude Code, with its Task tool in your tool list, start one in the background with this brief and nothing more, its placeholders filled in, once the rows `caption_cues.py` printed for the final cut are in a file, and go on with the motion graphics while it works:

> Write the caption moments that the section "Matching the captions" in `<this skill's SKILL.md>` describes, and nothing else. The caption kit is `<the frames directory>/caption-kit/`, `<a frame of the user's footage>` is a frame of the user's own footage at the canvas size, and the rows `caption_cues.py` printed for the final cut are in `<the rows file>`. Write the caption moments under `<the render-engine directory>/compositions/` and their font files under its `public/fonts/`, keep each matched part in `<the frames directory>/style/captions/` as `references/style-pack.md` says, never writing its `style.md`, and leave every other file alone. Stop when the caption moments match the kit, and report each caption host to mount, writing the same report to `<the report file>` as your last step. Ultrathink.

Mount and publish what it reports, unchanged, with your first publication after it reports; if the cut changes after you sent the rows, send it the new rows. If the rest of the edit is done before it reports, wait for the report file in steps of at most two minutes, each a command that returns as soon as the file appears, rather than ending your turn: a step taken after about five idle minutes pays for your whole context again. Codex starts no model subtask during an edit, and AI Producer Desktop has no Task tool.

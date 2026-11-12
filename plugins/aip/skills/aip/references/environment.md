# This computer

How an edit works on the computer behind this conversation: where the project's files live, how the footage starts its upload, what a local check may do, and what changes when a conversation has no computer or no command access. The [AI Producer skill](../SKILL.md) says when each part applies.
## Working folder

Every project, a new one or a change to an existing one, keeps the files you make on this computer in a working folder of its own. At its start, before you download or write anything for it, create a new folder in the current folder with `mktemp -d ./aip-XXXXXXXX`; where `mktemp` is missing, `python3 -c 'import tempfile; print(tempfile.mkdtemp(prefix="aip-", dir="."))'` (`py -3` in place of `python3` on Windows), or in PowerShell without Python `New-Item -ItemType Directory -Path "aip-$([guid]::NewGuid().ToString('N').Substring(0,8))"`. Name it by its full path from then on. Everything you make for the project goes under it: the local `render-engine/` workspace, a downloaded reference, preset or copy of the footage, reference frames and the caption kit, drafts and the checkpoint, a headless browser's profile, and every other scratch file. Never write to a fixed path, such as `/tmp/aipwork` or a `render-engine/` straight in the current folder, and never read or reuse a folder you did not create for this project unless the user hands it to you: another session can be editing on this computer at the same time, and a folder an earlier project left holds that project's files. The user's own files are read where they are.

## The footage upload

Start the PUT to the target `sign_upload` minted so that it runs on without holding you: the host's background execution, or [upload_batch.py](../scripts/upload_batch.py) given the source's folder as its root and the file name as `path`, left running.

## Checks on this computer

A page you check here before publishing stays inside this project, because other sessions run on the same computer.

**GSAP.** A page that animates loads this project's own copy. Read `render-engine/public/vendor/gsap.min.js` from this project with `get_workspace_file`, once and with no `max_chars`, since a window leaves out the rest of the file, and write the answer's `content` unchanged to `public/vendor/gsap.min.js` under the project's `render-engine/`. A host that saves a long answer to a file has written the answer's JSON there, so take `content` from that file with a short script instead of printing it. Fetch it in the main conversation and point helpers at the local copy. The service owns this file: never upload it, and declare it to preflight as [publication](publish.md#preflight) says.

**Where to look.** Do not search the whole disk for GSAP or a similar dependency (`find /`, `mdfind` and the like), and do not copy one out of another project's working folder: this project holds what its pages load. This does not limit looking for an installed font (`~/Library/Fonts`), a browser such as Playwright's, or a file the user named or described.

**A local server.** When a page has to be served, use a random high port and confirm the server is answering with this project's file before you trust a screenshot, since a port another session holds answers with that session's page:

```bash
WORK=<full path of the working folder>; SERVE=<directory to serve, inside it>; PAGE=<page, relative to SERVE>
PORT=$(python3 -c 'import random; print(random.randint(20000, 59999))')
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$SERVE" > "$WORK/server-$PORT.log" 2>&1 &
PID=$!; sleep 1
if kill -0 "$PID" 2>/dev/null && curl -fsS "http://127.0.0.1:$PORT/$PAGE" | cmp - "$SERVE/$PAGE"; then echo "http://127.0.0.1:$PORT/$PAGE pid $PID"; else cat "$WORK/server-$PORT.log"; kill "$PID" 2>/dev/null; fi
```

Keep the log rather than sending it to `/dev/null`: a failed start is reported there. When it does not print a URL, read the log and run the block again. Stop the server with `kill` and the pid it printed, and only that pid; `pkill -f` or killing by port also stops other sessions' servers. Where this shell is missing, such as PowerShell on Windows, follow the same steps with that shell's own commands and `py -3`. This server does not answer byte-range requests, so a video in the page cannot seek and stays on its first frame: put a still of that moment in its place for the check.

## A conversation with no computer

**The conversation has no computer behind it: nothing you can run a command on, nowhere to write a file, and a video the user attached is something the host holds rather than a file you have.** In ChatGPT that is a Chat conversation. This plugin edits in Work and in Codex, each of which gives the conversation a computer of its own; Chat does not, and nothing on the AI Producer side changes that. The upload the service signs waits for bytes only a computer can send, and the edit is authored as files only a computer can write, so do not sign an upload and do not start editing there. One thing does work in Chat: a video the user attached can become an AI Producer project, because the server downloads it itself. Start it that way, as steps 4 to 6 of the [setup skill](../../aip-setup/SKILL.md) describe, with the user's request as the goal, and ask nothing about its settings: they are applied where the edit happens. One video makes one project; when the user attached several, ask which to start with before you submit. Then give the user the project link and tell them that cutting, captions, and motion graphics need a Work chat or a Codex task: in ChatGPT on the web and in the desktop app, Work is the tab above the message box, and if it is not offered where they are, those two places have it. Ask them to start that conversation, mention AI Producer, and paste the project link. What carries over is what already reached AI Producer: a project keeps its footage and its edit behind its project link, so the new conversation takes the link and not the footage again. A follow-up on an existing project in Chat gets the same answer, without starting another project. ChatGPT Work, Codex, and Claude Code always have a computer, so this attachment-only flow never applies to them.

## Cursor without command or file access

**Cursor cannot run commands or edit files in this chat.** Tell the user this chat needs access to their video files and editing workspace. Ask them to switch to Agent mode with command and file access enabled, then resume the request with the existing project link when one exists. Do not sign an upload or start a project until that access is available, and do not send Cursor through the ChatGPT attachment-only flow or call `start_project_from_attachment` there. Once access is available, follow the ordinary upload and editing flow.

## The installed package

When a link in these skills points at a remembered versioned cache path that no longer exists, use the host's installed-plugin listing once to find the enabled package and its version, and resolve the link there.

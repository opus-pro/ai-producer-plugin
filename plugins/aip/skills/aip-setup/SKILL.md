---
name: aip-setup
description: "Set up AI Producer: connect the user's account, confirm the connection works, and start their first project from one video. Use only when the user chooses Set up for AI Producer, asks to get started with AI Producer or to continue AI Producer setup, or asks for help signing in to or connecting AI Producer. Do not use for an ordinary editing request once AI Producer is connected; that belongs to the aip skill."
---

# Set up AI Producer

This skill gets the user from a fresh install to one real AI Producer project, then stops. Its first success is a project AI Producer has accepted and started preparing, never an edited video. Everything after that, the cut, captions, and motion graphics, belongs to the [aip skill](../aip/SKILL.md).

It is safe to run again. Each time, start at step 1 and skip what is already done. In a new chat, "continue AI Producer setup" picks up where the user left off: a connection that already works skips steps 1 and 2, and a project this conversation already started skips straight to step 6 with it.

Talk to the user as the aip skill's Talk to the user section says: in their language, about their account and their video, never about tools, servers, codes, or this skill.

## Which conversation you are in

Decide this once, before step 1. A conversation has a computer behind it when you can run a command or write a file there: ChatGPT Work, Codex, and Claude Code always do. A ChatGPT Chat conversation does not: a video the user attaches there is something the host holds, not a file you have.

- **With a computer**, steps 1 to 3 run as written. Then hand over: carry the user's video and goal straight into the aip skill's new-project flow, which uploads the video, starts the project, and goes on to edit it. Steps 4 to 6 below do not apply; do not use the attachment tool there.
- **Without a computer**, all six steps apply. The video reaches AI Producer only as an attachment the server downloads, through `start_project_from_attachment`. Never ask the user to run a command, open a terminal, or upload from a computer of yours, and do not sign an upload.

## 1. Is AI Producer already connected?

Call `get_pricing` with no arguments. It is free, reads nothing from any project, and needs a signed-in connection, so it is the check. Keep its answer: step 4 reads it.

- **It answers with a price table:** the connection works. Say so in one line and go to step 3.
- **The AI Producer tools are not in your tool list, or the call is refused for sign-in** (the answer or the host says the connection needs to sign in, carries no credential, or its credential expired, was revoked, or is not recognized): the account is not connected. Go to the connect step below.
- **The call fails for any other reason** (the service is unreachable, a network error, a timeout, or a server fault): this is not a sign-in problem, and signing in again will not fix it. Tell the user AI Producer could not be reached just now, and that their account and video are not the problem. Check once more at most; if it still fails, ask them to try setup again in a few minutes. Do not send them to sign in.

### Connect the account

Connecting this client to AI Producer is its own step. Being signed in on the AI Producer website does not connect ChatGPT, Codex, or Claude Code, and connecting them does not need the website first: the connection opens an AI Producer sign-in page of its own. A user who already has an account signs in there; a new user creates one there.

The connection is something only the user can complete, in their own client. Name the step for the client they are on:

- **ChatGPT (Chat or Work):** when ChatGPT offers to connect AI Producer, choose Connect and finish signing in. If it does not offer, connect or reconnect AI Producer from Settings > Apps & Connectors and finish signing in there.
- **Codex:** run `codex mcp login ai-producer` in their own terminal and finish signing in. This holds in the Codex desktop app too, which has no sign-in control of its own for a plugin's connection; the commands you run reach no network, so you cannot do it for them.
- **Claude Code:** run `/mcp`, select `plugin:aip:ai-producer`, and finish signing in.

When a refusal carries its own recovery sentence, pass its meaning on in plain words alongside this step, since it is written for the client that called. Do not build an authorization link, do not suggest reinstalling the plugin, and do not change any MCP configuration: none of these connects the account, and each can break a working install. Then ask the user to tell you when they have finished, and wait.

## 2. Confirm the connection

When the user says they have connected, call `get_pricing` again. Only its answer counts: a user saying they signed in is not a connection, and neither is the website showing them signed in.

- **It answers with a price table:** tell the user in one line that AI Producer is connected, and go to step 3.
- **Still refused for sign-in:** the sign-in did not finish. Name the same step once more, and add only what the refusal says changed, such as an expired sign-in or an account that cannot use AI Producer. Ask a second time at most; after that, say setup is paused on the connection and that "continue AI Producer setup" resumes it.
- **The tools are still missing from your tool list:** this conversation did not pick up the new connection. Ask the user to start a new chat and say "continue AI Producer setup" there.
- **Any other failure:** handle it as in step 1. A failure after signing in is not a reason to sign in again.

## 3. The video and the goal

Ask for two things in one short message: one video, attached to the conversation, and one sentence on what they want from it, such as a 60-second highlight with captions. If the conversation already holds a video and a goal, use them and ask nothing. If it holds one of the two, ask only for the other.

That is the whole intake. Do not ask about style, captions, music, branding, or reference images here: the aip skill settles those when the edit starts. One video per project; when the user attaches several, ask which to start with.

## 4. Before you submit

Whether the video can be used is the service's to decide: its format, length, and size limits are checked when it is submitted, and a refusal says which one failed. Do not measure, transcode, or second-guess the video yourself, and do not quote limits from memory.

What starting costs is read from the `get_pricing` answer you kept, never from memory: the `start_project_from_attachment` row together with the billing detail. Follow the aip skill's pricing rule. When starting can charge this user, tell them in plain words what getting the video ready costs before you submit, and that the service measures the video's length to price it; when a daily quota may cover it first, say so. When it is free, say nothing about money.

## 5. Submit

Call `start_project_from_attachment` once:

- `file`: the video the user attached in this conversation. The host fills it in; never write a file object yourself or reuse one from an earlier attempt.
- `prompt`: the user's goal, in their own words.
- `aspect_ratio`: only when the user asked for one.

The call downloads the whole video before it answers, so it can take a while. Wait for it. Only an answer carrying `project_id` and `task_id` means the project exists; until then, say nothing about a project.

When it is refused, act on what the refusal says, once, and do not repeat the same call unchanged:

- **The attachment could not be downloaded** (no file arrived, or its address was refused): resending the same call fails the same way. Give the user both ways forward: attach the video again from ChatGPT on the web, or upload it on the AI Producer website and continue there.
- **Not a supported video, too long, or too large:** say which, as the refusal states it, and ask for a video that fits.
- **Credits, free usage, or the day's project limit:** say what ran out and when it resets, and pass on a top-up or upgrade link when the refusal carries one. Nothing was charged.
- **Busy, or a download that broke off and is marked retryable:** wait the time the refusal gives, then try once more. A second failure gets the same two ways forward as an attachment that could not be downloaded.
- **The connection needs to sign in again:** go back to the connect step in step 1.
- **Any other refusal:** say the project was not started and nothing was charged, unless the refusal says otherwise, and offer to try again later.

A call that ends with no answer at all, because it timed out or the connection dropped, is not a refusal: the project may have started anyway. Do not call again, and do not say it failed or that nothing was charged. Look for it with `list_projects`; a project for this video that appeared since you submitted is the one, so continue to step 6 with its link. If none is there yet, tell the user the start may still be going through and that the AI Producer website will show the project once it has. When they ask to try again, look with `list_projects` once more; if it is still not there, tell them that a start which did go through would make a second project, which can be charged again, and submit again only when they say to go ahead knowing that.

## 6. Hand over

Once the answer carries a project, tell the user, in this order:

1. Their project is in AI Producer and the video is being prepared. It is not edited yet: preparing the footage is the first step before the cut.
2. The project link, `page_url` from the answer, exactly as returned. It is theirs to keep and works from any browser. Never give out `agent_page_url`.
3. Where to continue. Cutting, captions, and motion graphics need a conversation with a computer: a ChatGPT Work chat or a Codex task. They start it, mention AI Producer, and paste the project link; the footage is already in AI Producer, so they do not attach it again.

Then setup is done. Do not call this skill again in the conversation. If the user asks how preparation is going, read it with `get_task` and answer from what it says.

# Starting one project from several videos

Read this when `start_transcribe_project` lists a `video_refs` argument and the user gives you more than one video for one edit. When the tool lists no `video_refs`, the service cannot start from several videos yet: start from one video as the [AI Producer skill](../SKILL.md) says, and tell the user which one you started with.

Several videos the user gives for one edit make one project: interviews to cut together, takes of the same talk, or a set of clips of equal weight. Start a separate project for each only when the user asks for separate videos.

## Order

The order of `video_refs` is the order the videos play in the cut, so it is the order the user gave them in. When the user names an order, by numbering, by the words they use or by file names that count up, use that order. Do not ask about the order otherwise.

## Upload and start

1. Sign one upload per video with `sign_upload`, each with that file's own sha256 and size, in the turn the footage arrives.
2. PUT every file to its own target, together: the host's background execution, or [upload_batch.py](../scripts/upload_batch.py) given every file at once. A failed or interrupted PUT is sent again to the same target, as for one video.
3. When every PUT has finished, call `start_transcribe_project` once. `video_ref`, `sha256` and `filename` are the first video's. `video_refs` lists every video in order, each as `{video_ref, sha256, filename}`, and its first entry repeats the first video.

The service checks every video by the rules one video meets, including the length limit for each file, and starts the project only when every video passes. Read what preparation costs from `get_pricing`, as the skill says for one video.

## A refused video

A refusal about one video names it: its position (`source_position`) and `filename` lead the error, and the rest of the refusal is the one that video would get alone. Nothing was started, claimed or held, so there is no project to clean up.

Tell the user which video was refused and why, in one sentence each. Then fix what the refusal names, for example by uploading that file again, and send the whole start again with every video. Leave a video out only when the user agrees, and never start from part of the set without saying so.

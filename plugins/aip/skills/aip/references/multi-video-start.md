# Starting one project from several videos

Read this when `start_transcribe_project` lists a `video_refs` argument and the user gives you more than one video for one edit. When the tool lists no `video_refs`, the service cannot start from several videos yet: start from one video as the [AI Producer skill](../SKILL.md) says, and tell the user which one you started with.

Several videos the user gives for one edit make one project: interviews to cut together, takes of the same talk, or a set of clips of equal weight. Start a separate project for each only when the user asks for separate videos.

## Order

The first video is the project's main video. It is the only video `frame_speaker` measures, and it is always transcribed and always in the first draft: `transcribe: false` or `place: false` on its entry is refused. So list the main speaking video first, the one whose speaker the edit frames, even when the user gave it later.

The first draft plays the videos one after another in the order of `video_refs`. After the first video, keep the order the user gave them in: when the user names an order, by numbering, by the words they use or by file names that count up, use that order. Do not ask about the order otherwise.

A later video the user calls B-roll or a cutaway, or one meant to cover the speaker rather than play after them, takes `"place": false`: it is prepared and stays in the project, out of the first draft. Give it `"transcribe": false` too when it has no speech worth captioning (below). A later video plays by its `path` in the editing script's `sources` list (`public/sources/<id>.mp4`), in place of the speaker or over them. In place of the speaker, `place_source_video` puts the whole video at the end of the cut, and a part of it plays anywhere as a speaker clip pair whose video `src` is that path and whose audio `src` is the same path ending in `.mp3`, replacing the speaker's seconds it covers. To cover the speaker with a few seconds of a later video while the narration keeps playing, add a muted root clip on its own track whose src is that video's path from the editing script's sources list (public/sources/<id>.mp4): `<video id="<unique>" class="clip" data-track-index="<n>" src="public/sources/<id>.mp4" data-start data-duration data-media-start muted playsinline data-volume="0">`, with data-media-start plus data-duration inside that video's length. Do not use a speaker clip pair for this: a speaker clip replaces the speaker's sound as well as the picture.

## Upload and start

1. Sign one upload per video with `sign_upload`, each with that file's own sha256 and size, in the turn the footage arrives.
2. PUT every file to its own target, together: the host's background execution, or [upload_batch.py](../scripts/upload_batch.py) given every file at once. A failed or interrupted PUT is sent again to the same target, as for one video.
3. When every PUT has finished, call `start_transcribe_project` once. `video_ref`, `sha256` and `filename` are the first video's. `video_refs` lists every video in order, each as `{video_ref, sha256, filename}`, plus `"transcribe": false` on a later video that needs no transcript (below), and its first entry repeats the first video.

## Videos with no talking

Transcribing a video costs time, and for a long project money, so transcribe only the videos whose words the edit needs. A later video the user calls B-roll, a cutaway, an establishing shot, or a clip with no talking, or one they say has no speech, takes `"transcribe": false` in its `video_refs` entry. Decide from the user's words, never from the file name or a guess at what the picture shows; when they say nothing about a video, leave `transcribe` out and it is transcribed.

A video started without a transcript still plays and cuts like any other, but has no captions and no words to cut by. When the user later wants its words (captions on it, or cutting it by what is said), call `start_source_transcript` with the project and that video's `source_id`, then poll its `task_id` with `get_task`. A repeat call while it runs, or after it finished, starts nothing.

`get_transcript` on such a project lists every video under `sources` with its `transcript_state` and says whether the transcript is `complete`. `not_requested` means the video was never transcribed, not that nobody speaks in it: do not tell the user a video has no speech unless its state is `no_speech`, and never describe a transcript with `complete: false` as the whole project's.

The service checks every video by the rules one video meets, including the length limit for each file, and starts the project only when every video passes. Read what preparation costs from `get_pricing`, as the skill says for one video.

## A refused video

A refusal about one video names it: its position (`source_position`) and `filename` lead the error, and the rest of the refusal is the one that video would get alone. Nothing was started, claimed or held, so there is no project to clean up.

Tell the user which video was refused and why, in one sentence each. Then fix what the refusal names, for example by uploading that file again, and send the whole start again with every video. Leave a video out only when the user agrees, and never start from part of the set without saying so.

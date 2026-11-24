# Writing caption cues

Read this when a caption look shows one word at a time, when the speech's transcript words are a character or two each, or before you merge, split or correct a cue. The [dynamic caption skill](../SKILL.md) owns timing, mounting and legibility.

## How many words a cue shows

`--max-words` on [caption_cues.py](../../aip/scripts/caption_cues.py) is how many words a cue shows at once: 4 by default, 1 for a look that shows one word at a time, and 8 to 12 for speech whose transcript words are a character or two each, such as Chinese or Japanese.

## Changing a cue

You may merge two cues or split one at a word boundary, using the words' own times, and correct a word's spelling, casing or punctuation; never change what was said.

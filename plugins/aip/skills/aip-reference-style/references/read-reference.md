# Reading a reference without a style pack

This file is for a reference whose folder holds no `style/style.md`, as the [reference style skill](../SKILL.md#read-the-reference) says. A reference whose pack is an edit's own (`Pack: edit`) reads only its contact sheets and transition pages here, and makes no caption kit.

## Read the stills

Unless the folder already holds `reference-index.json`, run [reference_frames.py](../scripts/reference_frames.py) with the reference video, or the directory of reference images, and a new directory in the project's working folder, outside its `render-engine/`. For a video it writes the stills you read the style from and `reference-index.json`, which names each file with the times it covers:

- `contact-sheet-NN.jpg`: the analyzed span at two frames a second, each frame labeled with its time.
- `transitions-NN.jpg`: one row per change of shot between beats, twelve frames a second across the cut. Each boundary in the index carries a `kind` read from the frames' brightness and change: `cut` (one frame to the next, nothing between), `flash` (the frames brighten across the cut, toward white or a colour, as in a flash or a light leak), or `blur` (both shots smear where they meet, as in a whip or a blur).
- `strips/beat-NN.jpg`: each beat at up to four frames a second, for how a treatment enters, moves and leaves.
- `keyframes/beat-NN.jpg`: one larger frame per beat, for type, color and layout detail.

A long reference is analyzed in windows: its opening and windows spread evenly over the rest, up to the script's budget, so the sample keeps the reference's own mix of quiet and busy stretches. `partial` and `analyzed` in the index say when that happened, and `cuts_per_minute` gives the cutting rate over the whole reference beside the rate in the windows; read proportions from the windows against those rates.

Read every contact sheet first, then every transition page, then the strips and keyframes of the beats that carry a distinct treatment; of a reference of stills, read every still. These stills are input analysis: they are never staged, uploaded, or drawn into the edit.

## The caption kit

When the reference shows captions, pick by their time labels, while you read the contact sheets, what the captions will be matched against: a moment for each distinct treatment the captions use, two to four in all (a plain line, an emphasized word, a stacked line, a colour or a fill the picture shows through), each paired with a moment of the same shot without a caption, or with the least of one; the moment just before a caption arrives; and the band of the frame height the captions sit in. Run the script again on the same directory with them, `--caption-kit <caption>:<clean>,... --band <top>:<bottom> --entry <seconds>`. It writes `caption-kit/`: those frames at the reference's own resolution, and `kit.jpg`, their caption bands side by side above the band frame by frame as a caption arrives. Read `kit.jpg` once and replace a pair that does not show what you picked it for. The kit is everything the captions are matched against, once the cut is final, as [Matching the captions](#matching-the-captions) says. A reference that shows no captions gets no kit. A reference of stills names stills by number instead of times, `--caption-kit <still>[:<still>],... --band <top>:<bottom>`: each still that shows a caption, with a still of the same shot without one when the images include it, and no `--entry`, since a still shows no caption arriving. A preset's folder already holds its kit when the preset shows captions; make no other.

## Its own pack

A reference the user brought keeps what the edit matches in its own pack, an edit's pack, as the [style pack](style-pack.md) says: each caption part as its step 2 says, each kind of graphic you write as its step 3 says, with one comparison against its visual, and `style.md` as its step 4 says.

## Matching the captions

Once the cut is final and the rows `caption_cues.py` printed are in a file, as the skill's [Matching the captions](../SKILL.md#matching-the-captions) says, the captions are matched against the kit. Where [tools.md](tools.md) gives this match to a subagent on this host, do as it says. Elsewhere write the captions yourself at that point, the same way.

The captions are matched against the caption kit alone. Read `kit.jpg` once; the kit's frames are the only reference pictures you open, and only to compare with or to measure as below: no contact sheet, strip or keyframe, and never the reference video. Of this package, read this skill, its [tools.md](tools.md), the dynamic caption skill, the composition contract, the [style pack](style-pack.md) and the [aesthetic rules](../../aip/references/aesthetic-rules.md), and no other file, scripts included.

1. Settle the faces. `specimen` sets a kit caption's own words in every installed face of the families you name, under that caption; pick each part's face from that one image, and `extract` it as a font file.
2. Match the look like for like before writing any caption moment: a page at the kit frame's size that mounts, over that pair's clean frame, the caption's parts built the way the edit's will be, with the kit caption's own words. Run `compare` with the caption frame, which sets the two side by side cropped to the caption band at full resolution, read that image, change what differs, and run it again, until the two cannot be told apart, for each pair in the kit. Face, weight, size, tracking, colour and position are read from that image, never measured. A look includes how its text sits on the picture: solid over it, letting the picture show through it, or blending with it. A part that lets the picture through or blends does so over any picture, so draw it that way, never as colours that copy what one frame shows behind it, and keep one styling for each treatment across every kit pair that shows it. Only for such a part, or one the image leaves open, measure how its pixels follow the picture beneath, and where the kit has no clean frame of its shot, make one from the caption frame by masking the caption and filling it from around it. Measure nothing else.
   Keep each part that matches as `style/captions/<treatment>-<part>.html` in the reference's folder, as the style pack says, and describe each treatment in the report the way `style.md`'s Captions section does; the edit writes `style.md` from that report.
3. Write every caption moment from the rows the same way, taking how a caption arrives from the kit's last row (a kit from stills has none, so the dynamic caption skill's entry stands), then check one over the user's frame as the skill's [Matching the captions](../SKILL.md#matching-the-captions) says.

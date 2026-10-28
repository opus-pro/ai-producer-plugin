# A reference's style pack

A reference folder may hold `style/`: the reference already read into a style and matched against the reference, so an edit copies it instead of reading and matching the reference again. A preset's folder carries one when the preset was built with it. An edit writes one for a reference it read itself, into that reference's folder, so a later edit with the same reference starts from it.

## What it holds

- `style/style.md`, read first. Its first line is `Pack: whole` for a pack that holds every caption treatment and every kind of graphic the reference shows, or `Pack: edit` for an edit's pack. It has four sections:
  - `## Captions`: each treatment by name, with its template files under `style/captions/`; which cues take it and about how often; where it sits, against the speaker (below the chin, at chest height) and against the frame; how it enters and leaves; what its host carries (its track order among the caption parts, a blend or a backdrop filter); and each font face with where it comes from.
  - `## Motion graphics`: each kind of graphic by name, with its template under `style/motion/`; the visual it copies (a `visuals/` file and its time in the reference); what it shows; its slots, the text and imagery an edit replaces with the user's own; how long it holds; and how often, and where in the runtime, the reference uses it.
  - `## Transitions and rhythm`: each transition the reference uses and how often; the cutting rate and how reframes carry it over one continuous shot; and the share of the runtime under graphics against the speaker alone.
  - `## Leave out`: the reference's own content and platform furniture that no template carries.
- `style/captions/<treatment>-<part>.html`: one caption moment per part of a treatment, since each part is its own host as [Matching the captions](../SKILL.md#matching-the-captions) says (a treatment of one part drops `-<part>`), under the [dynamic caption skill](../../aip-dynamic-caption/SKILL.md), with the kit caption's own words. Its composition id is `tpl-<file name>`. `style.md` lists every part file of a treatment with what its host carries.
- `style/motion/<kind>.html`: one composition per kind of graphic, under the [composition contract](../../aip-composition/SKILL.md), holding sample content of the shape its slots take. Its composition id is `tpl-<file name>`.
- `visuals/visual-<seconds>.jpg`: each graphic at the reference's own resolution, written by `reference_frames.py <reference video> <folder> --visuals <seconds>,...`. A reference of stills has no `visuals/`: its `stills/` are already each image at its own resolution, and `style.md` names them instead.

The pack carries no font files: `style.md` names each face and how to get it, an installed family split out with `caption_compare.py extract` or an open family's download, and the edit stages it as the reference style skill says.

## Using it

An edit copies a template once per host: it renames every `tpl-<name>` in the file to the host's own id, replaces the cues or the slots with the user's words, times and imagery, and keeps everything else, the CSS, the structure and the motion, as the template has it. A template is the reference read in advance, so it ranks where the reference does: the user's own words and the AI Producer skills' rules (legibility, safe area, the caption and composition contracts) outrank it, and a template changes wherever they ask for something else. Which treatments and graphics an edit uses, where and how often, is still decided from the user's content each time. The host carries what `style.md` says its treatment's host carries. Geometry the user's frame decides (a band against the user's chin, a seat beside the user's face) is set from the user's frame, keeping the treatment's character, as the [framing skill](../../aip-framing/SKILL.md) says.

## Building it

The same steps build a whole pack and an edit's own:

- **A whole pack** is built once for a preset, before it is published: every caption treatment and every kind of graphic the reference shows. A person opens the templates in the editor before the preset is published, and nothing is published they have not checked.
- **An edit's pack** holds what the edit copies: every caption treatment the kit shows, since the caption match matches them all, and only the kinds of graphic the edit uses, so a later edit still reads the reference for the rest. Its captions are matched exactly as below; each graphic takes one comparison in step 4, changing what it shows differs, with no second round unless the first shows the graphic broken.

One writer owns `style.md`. In an edit the caption match writes only `style/captions/` and describes its treatments in its report, and the edit writes `style.md` once that report is in, so the two never overwrite each other.

1. Read the reference as the reference style skill says: its contact sheets and transition pages, and its caption kit when it shows captions.
2. For each distinct graphic, take its clearest moment from the contact sheets' time labels, and run `reference_frames.py --visuals` with all of them at once. Read each visual once. A reference of stills skips this step: each graphic's visual is its still.
3. Captions: match each treatment against the kit as steps 1 and 2 of [Matching the captions](../SKILL.md#matching-the-captions) say, and keep each matched part as `style/captions/<treatment>.html`.
4. Motion graphics: write each kind as a composition with the reference's own layout, type, palette and motion, from its visual and its beat's strip. Render it beside its visual with `caption_compare.py compare <out.png> <visual>=<page> --t <seconds>`, from a page that mounts the template and seeks its timeline to `?t`, and change what differs until the two cannot be told apart. Its content is sample content of the same shape: never the reference's words, brands, people or screens.
5. Write `style.md`, naming every file the pack holds. In an edit it is written once the caption report is in, or as soon as the graphics are written when the reference shows no captions and nothing reports. A pack holds only `style/style.md`, `style/captions/<name>.html`, `style/motion/<name>.html` and `visuals/visual-<seconds>.jpg`: no fonts, images of the user's, or working files.

# Smart Money After 50

YouTube channel for people over 50 in the USA and Canada who watch on a TV. Faceless long-form videos (15–30 minutes, about 20) on money after 50, as numbered lists of changes, mistakes, habits and regrets. Four videos a week. No Shorts. Built with HyperFrames; every tool is local or free.

Each video lives in `videos/<NNN-slug>/`. `videos/001-social-security-2027/` is the reference video: copy its file shapes.

## Making a video

Run every command from the repo root. `PY` is a Python with Playwright, faster-whisper, Pillow and requests (`C:\code\youtube\.venv\Scripts\python.exe`). Chatterbox runs in its own Python (`CHATTERBOX_PYTHON`, default `C:\code\2d\tools\.venv\Scripts\python.exe`).

1. **Topic.** A title with a real deadline or a real dollar amount in it ("before January", "$75 a month"). The user picks from 5 candidates. Done when the user has picked.
2. **Research.** `PY pipeline/page_text.py <url> videos/<id>/sources/<name>.txt` for each source, then write `research.md`: one table row per claim, with the exact words from the saved page. Done when every number the script will use has a row, or is listed under "Not yet verified".
3. **Script.** `script.md`: `## hook` (60–90 words: the promise, then what the viewer will know by the end), `## intro` (empty: the slot for the channel intro), then one `## <id>` section per list item. Write numbers the way they are shown on screen (`3.6%`, `$75`); `say.json` maps each to how it is spoken. About 135 words a minute outside the hook. Done when every number in the script appears in `research.md` with its source words, and the user has approved the script.
4. **Voice.** `PY pipeline/check_say.py videos/<id>` until it names no missing pronunciation. Then `PY pipeline/voice.py videos/<id>`, then `PY pipeline/words.py videos/<id>/assets/audio/voice.wav videos/<id>/words.json`, then `PY pipeline/align.py videos/<id>`. Done when `align.py` reports fewer than 5% of words "estimated"; more means the voice misread something: fix `say.json` and re-voice that section.
5. **Media.** Stock: `PY pipeline/stock.py photo|video "<words>" videos/<id>/assets/stock 4`. Pages: `PY pipeline/screenshot.py <url> videos/<id>/assets/shots/<name>.png "<phrase>" ...` with every phrase the narration will point at. Look at each photo and each clip's `.preview.jpg` before using it. Done when every shot planned in step 6 has a file you have looked at.
6. **Shots and sound.** `visuals.json`: see "Shot list" below. Then `PY pipeline/mix_audio.py videos/<id>`, `PY pipeline/build_captions.py videos/<id>` and `PY pipeline/build_scenes.py videos/<id>`. Done when the build prints no WARNING and reports one shot about every 4 seconds per section.
7. **Check.** In `videos/<id>`: `npm run check` must pass, then `npx hyperframes snapshot --at <one time inside every shot>` and read every contact sheet. Done when every shot is readable, shows what the narration is saying at that moment, and no text sits on a face or under the caption line.
8. **Render.** `npx hyperframes render --output ../../<name>.mp4` from the video folder. Hand it to the user on `questions.html` with what to check while watching.
9. **Upload kit.** Write `upload.json` (3 titles, summary, a chapter name per section, sources, disclaimer, tags) and `thumbnail.html` (1280x720: one photo, three or four huge words). Then `PY pipeline/upload_kit.py videos/<id>` and `PY pipeline/thumbnail.py videos/<id>`. Done when `upload_kit.py` prints no FIX line and you have looked at `thumbnail.jpg`. The user uploads the video themselves.

## Channel rules

- **Sources.** Every number on screen or in the voice comes from the saved text of an official or primary page, quoted in `research.md`. A search summary is a lead to follow, not a source.
- **Urgency is real.** Deadlines and dollar amounts come from the sources. A title promises only what the video proves.
- **Blocked sites stay blocked.** `screenshot.py` and `page_text.py` identify themselves honestly and report `BLOCKED` when a site refuses automated visitors. Use another official copy of that fact:
  - ssa.gov is blocked. SSA news releases are readable on `content.govdelivery.com`.
  - federalregister.gov and ecfr.gov pages show a captcha. Federal Register notices are readable on `govinfo.gov` (`/content/pkg/FR-<date>/html/<number>.htm`). Regulation text comes from the eCFR API, which is meant for programs: `curl --compressed "https://www.ecfr.gov/api/versioner/v1/full/<date>/title-20.xml?part=404&section=404.435"`. A regulation has no screenshot, so show it as a `number` or `statement` shot with the section in the `note` ("Source: 20 CFR 404.435").
  - irs.gov is readable.
  - On a plain-text page such as govinfo's, a phrase for `screenshot.py` must sit on one line of the page.
- **Deadlines that pass.** Word a date so the sentence stays true after it ("people who enrolled by November 18 see it first").
- **Faces and brands.** Stock people only. Choose clips with no visible company logos.
- **Voice.** One narrator, copied by Chatterbox from `voices/narrator_ref.wav`, a synthetic reference. Hook at 1.05×; everything else at 0.85× with 0.5 s between sentences and 1.2 s between paragraphs (`PACE` in `voice.py`).
- **Sound.** `mix_audio.py` makes the one audio track: the voice is compressed, the music has its mid-range (500 Hz–2 kHz) cut, sits 25 dB under the voice's peak, and ducks further while the narrator speaks. Music comes from `music/` (not in git: add your own files). Calm tracks only: no hip-hop.
- **Charts are honest.** Bars are drawn to true scale. When two values would look the same height, show the difference as a `number` shot ("+$72 a month") instead of bars.

## Look

Black background, cream text `#f4eedd`, red `#d23232` for titles, list numbers and warnings. Rising chart lines and gains are cream or green; red on a chart means a loss. Serif (Playfair Display) for titles and big numbers, Inter for everything else. Text is sized to read from a sofa: nothing under 30 px.

Every video has, in this order: hook (20–30 s), the channel intro (6 s, `pipeline/templates/intro.html`), then the sections. Captions run under all narration and a particle overlay runs over the whole video; `build_scenes.py` adds both.

## Shot list

`visuals.json` is `{"music": "<file in music/>", "sections": {"<section id>": [shot, ...]}}`. A shot starts when its `"at"` phrase is spoken and lasts until the next shot. Copy `"at"` phrases from that section of `script.md`; the first shot of a section needs none. Aim for 4 seconds a shot: `build_scenes.py` warns above 7 s and stops below 1 s.

About one shot in three is a `video`; the rest are photos, articles and cards. When the narration states a fact from a page, the shot is that page as an `article` with the words marked.

| `type` | Fields | Shows |
|---|---|---|
| `photo` | `src`, `side` (`left`/`right`), `zoom` (`in`/`out`, alternates by default), `text` | Full-screen photo, slowly zooming, text on the side away from faces |
| `video` | `src`, `side`, `text` | Full-screen silent clip (10 s at most) with text on top |
| `article` | `src` (a screenshot from `screenshot.py`), `view` (`x`, `y`, `width` in image pixels: the part of the page that fills the screen), `marks`, `source`, `pan` | The real page, each mark swept in yellow as the narrator reaches it |
| `number` | `value`, `at_value`, `text`, `note` | One huge number with a line under it; `note` is the source |
| `statement` | `text` | One sentence, centred |
| `tiles` | `title`, `tiles` (text, or `null` for a hidden "?") | The numbered list, some items still hidden |
| `bars` | `title`, `bars` (`label`, `display`, `value`, `strong`, `at`), `delta`, `delta_at`, `note` | Bars drawn to scale, with the difference in green |

`text` is a list of lines `{"style": "num"|"big"|"text"|"small"|"statement", "text": "...", "at": "<phrase>"}`. A line appears when its `at` phrase is spoken, or in order after the shot starts. `*stars*` put words in red. A mark is `{"phrase": "<as given to screenshot.py>", "boxes": [<indexes into that phrase's boxes in the .json>], "at": "<phrase>"}`; a phrase that wraps onto two lines has two boxes.

## Gotchas

- Whisper runs on the CPU: the CUDA libraries it needs are missing and the GPU attempt can hang.
- `voice.py` re-voices only sections whose text, pronunciation or pace changed. Delete `audio/<section>.raw.wav` and `.hash` to force one.
- Chatterbox takes about 4 seconds per second of speech. Voice a whole video in the background.
- `say.json` must cover every token containing a digit, `$` or `%`; `voice.py` stops and names the missing ones.
- Openverse and Wikimedia rate-limit and return small images. Stock comes from Pexels; the key is the `pexel-api` line in `.env`.
- A scene's host id, root `data-composition-id` and timeline key must match, or the render waits 45 s per scene and shows still frames. `build_scenes.py` keeps them equal to the section id, so keep section ids free of spaces.
- End every reply to the user by rewriting `questions.html` in the repo root (see the user's global rules).

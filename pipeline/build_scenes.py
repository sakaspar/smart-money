"""Build the HyperFrames project for a video from its shot list.

  build_scenes.py <video_dir>

Reads visuals.json, aligned.json and sections.json. Writes index.html, one scene per section in
compositions/, the intro and the particle overlay. The sound comes from mix_audio.py.

A shot starts when its "at" phrase is spoken (the phrase must be copied from that section of the script)
and lasts until the next shot. The shot types and their fields are listed in AGENTS.md.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "pipeline" / "templates"
LEAD_S = 0.15              # a shot cuts in just before its phrase
MIN_SHOT_S = 1.0
LONG_SHOT_S = 7.0           # longer than this is too slow for the channel: warn
MARK_PAD = 4

STYLE = """
    #root { position: absolute; inset: 0; overflow: hidden; background: #000; font-family: "Inter", sans-serif;
      --ink: #f4eedd; --accent: #d23232; --mark: #ffe14d; --up: #5fbf7f; }
    .sc-shot { position: absolute; inset: 0; overflow: hidden; color: var(--ink);
      background: radial-gradient(ellipse 70% 60% at 50% 40%, #1c1c1c 0%, #000 100%); }
    .sc-shot.sc-clear { background: none; }
    .sc-video { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }
    .sc-photo { position: absolute; inset: 0; }
    .sc-photo img { position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: cover; }
    .sc-over { position: absolute; top: 140px; width: 860px; display: flex; flex-direction: column; gap: 16px; isolation: isolate;
      text-shadow: 0 3px 6px rgba(0, 0, 0, 0.95), 0 0 26px rgba(0, 0, 0, 0.9), 0 0 70px rgba(0, 0, 0, 0.75); }
    /* No panel: a soft dark glow behind the words keeps them readable on bright photos. */
    .sc-over::before { content: ""; position: absolute; left: -160px; top: -130px; right: -120px; bottom: -150px; z-index: -1;
      background: radial-gradient(ellipse 50% 50% at 50% 50%, rgba(0, 0, 0, 0.62) 0%, rgba(0, 0, 0, 0.4) 45%, rgba(0, 0, 0, 0) 100%); }
    .sc-over.left { left: 110px; }
    .sc-over.right { left: 950px; }
    .sc-num { font-family: "Playfair Display", serif; font-weight: 700; font-size: 190px; line-height: 0.95; color: var(--accent); }
    .sc-big { font-family: "Playfair Display", serif; font-weight: 700; font-size: 120px; line-height: 1; }
    .sc-text { font-size: 66px; font-weight: 700; line-height: 1.14; }
    .sc-small { font-size: 46px; font-weight: 700; line-height: 1.22; }
    .sc-paper { background: #fff; }
    .sc-pan { position: absolute; left: 0; top: 0; }
    .sc-page { position: absolute; left: 0; top: 0; transform-origin: 0 0; }
    .sc-page img { position: absolute; left: 0; top: 0; }
    .sc-mark { position: absolute; background: var(--mark); mix-blend-mode: multiply; border-radius: 4px; }
    .sc-source { position: absolute; left: 60px; top: 44px; padding: 12px 24px; border-radius: 12px;
      background: rgba(0, 0, 0, 0.85); color: var(--ink); font-size: 32px; font-weight: 700; }
    .sc-center { position: absolute; left: 160px; top: 150px; width: 1600px; height: 700px; display: flex;
      flex-direction: column; align-items: center; justify-content: center; gap: 26px; text-align: center; }
    .sc-hero { font-family: "Playfair Display", serif; font-weight: 700; font-size: 300px; line-height: 0.95; }
    .sc-statement { font-family: "Playfair Display", serif; font-weight: 700; font-size: 128px; line-height: 1.08; }
    .sc-statement em, .sc-text em, .sc-big em { font-style: normal; color: var(--accent); }
    .sc-rule { width: 140px; height: 8px; background: var(--accent); }
    .sc-title { position: absolute; left: 0; top: 110px; width: 1920px; text-align: center;
      font-family: "Playfair Display", serif; font-weight: 700; font-size: 104px; }
    .sc-title span { display: inline-block; }
    .sc-title em { font-style: normal; color: var(--accent); }
    .sc-tile { position: absolute; top: 350px; width: 400px; height: 440px; border-radius: 18px;
      border: 3px solid rgba(244, 238, 221, 0.28); background: #141414; padding: 30px 34px; }
    .sc-tile .n { font-family: "Playfair Display", serif; font-weight: 700; font-size: 150px; line-height: 1; color: var(--accent); }
    .sc-tile .t { margin-top: 26px; font-size: 46px; font-weight: 700; line-height: 1.15; }
    .sc-tile .q { display: inline-block; margin-top: 6px; font-family: "Playfair Display", serif; font-size: 150px;
      line-height: 1; opacity: 0.35; }
    .sc-bars { position: absolute; left: 0; top: 300px; width: 1920px; height: 560px; }
    .sc-bar { position: absolute; bottom: 70px; width: 320px; border-radius: 10px 10px 0 0; background: var(--ink); opacity: 0.45; }
    .sc-bar.strong { opacity: 1; }
    .sc-bar-value { position: absolute; width: 480px; text-align: center; font-family: "Playfair Display", serif;
      font-weight: 700; font-size: 84px; }
    .sc-bar-label { position: absolute; bottom: 0; width: 480px; text-align: center; font-size: 42px; font-weight: 700; opacity: 0.85; }
    .sc-delta { position: absolute; left: 0; top: 250px; width: 1920px; text-align: center;
      font-family: "Playfair Display", serif; font-weight: 700; font-size: 92px; color: var(--up); }
    .sc-note { position: absolute; left: 0; top: 860px; width: 1920px; text-align: center; font-size: 30px; opacity: 0.7; }
"""

SCRIPT_HEAD = """
    const tl = gsap.timeline({ paused: true });
    const land = (selector, at) => tl.fromTo(selector, { opacity: 0, x: 30, filter: "blur(10px)" },
      { opacity: 1, x: 0, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }, at);
    const pop = (selector, at) => tl.fromTo(selector, { opacity: 0, scale: 0.8 },
      { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.7)" }, at);
    const zoom = (selector, at, duration, from, to) => tl.fromTo(selector, { scale: from }, { scale: to, duration, ease: "none" }, at);
    const sweep = (selector, at) => tl.fromTo(selector, { scaleX: 0, transformOrigin: "0 50%" },
      { scaleX: 1, duration: 0.55, ease: "power2.out" }, at);
    const grow = (selector, at) => tl.fromTo(selector, { scaleY: 0, transformOrigin: "50% 100%" },
      { scaleY: 1, duration: 0.8, ease: "power3.out" }, at);
    const drift = (selector, at, duration, to) => tl.fromTo(selector, { y: 0 }, { y: to, duration, ease: "none" }, at);
"""


def plain(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def rich(text: str) -> str:
    """Escapes text; *stars* mark the words shown in the accent colour."""
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(text))


class Section:
    """One section of the script: finds when a phrase is spoken, always searching forward."""

    def __init__(self, span: dict, words: list[dict]):
        self.id, self.start, self.end = span["id"], span["start"], span["end"]
        self.words = words
        self.cursor = 0

    def when(self, phrase: str, advance: bool = True) -> float:
        wanted = [plain(w) for w in phrase.split() if plain(w)]
        spoken = [plain(w["word"]) for w in self.words]
        for index in range(self.cursor, len(spoken) - len(wanted) + 1):
            if spoken[index:index + len(wanted)] == wanted:
                if advance:
                    self.cursor = index
                return self.words[index]["start"]
        sys.exit(f'visuals.json: "{phrase}" is not spoken in section {self.id} after the previous shot')


class Scene:
    def __init__(self, section: Section):
        self.section = section
        self.html: list[str] = []
        self.js: list[str] = []

    def local(self, absolute: float) -> float:
        return round(absolute - self.section.start, 3)

    def line_times(self, lines: list[dict], start: float, end: float) -> list[float]:
        times = []
        for index, line in enumerate(lines):
            if "at" in line:
                moment = self.section.when(line["at"], advance=False) - 0.1
            else:
                moment = start + 0.3 + 0.55 * index
            read_time = 0.6 + 0.3 * len(line["text"].split())
            times.append(self.local(max(min(moment, end - read_time), start + 0.1)))
        return times

    def overlay(self, shot_id: str, shot: dict, start: float, end: float) -> str:
        lines = shot.get("text", [])
        if not lines:
            return ""
        rows = []
        for index, moment in enumerate(self.line_times(lines, start, end)):
            style = lines[index].get("style", "text")
            rows.append(f'<div id="{shot_id}-t{index}" class="sc-{style}">{rich(lines[index]["text"])}</div>')
            self.js.append(f'{"pop" if style == "num" else "land"}("#{shot_id}-t{index}", {moment});')
        return f'<div class="sc-over {shot.get("side", "left")}">{"".join(rows)}</div>'

    def clip(self, shot_id: str, start: float, end: float, extra: str = "") -> str:
        return (f'id="{shot_id}" class="sc-shot{extra} clip" data-start="{self.local(start)}" '
                f'data-duration="{round(end - start, 3)}" data-track-index="1"')

    def photo(self, shot_id, shot, start, end, number):
        direction = shot.get("zoom", "in" if number % 2 == 0 else "out")
        ends = (1.02, 1.12) if direction == "in" else (1.12, 1.02)
        self.html.append(
            f'<div {self.clip(shot_id, start, end)}><div class="sc-photo" data-layout-allow-overflow>'
            f'<img id="{shot_id}-img" src="assets/{shot["src"]}" alt="" /></div>{self.overlay(shot_id, shot, start, end)}</div>')
        self.js.append(f'zoom("#{shot_id}-img", {self.local(start)}, {round(end - start, 3)}, {ends[0]}, {ends[1]});')

    def video(self, shot_id, shot, start, end, number):
        self.html.append(
            f'<video id="{shot_id}-vid" class="sc-video clip" data-start="{self.local(start)}" data-duration="{round(end - start, 3)}" '
            f'data-track-index="0" muted playsinline src="assets/{shot["src"]}"></video>')
        self.html.append(f'<div {self.clip(shot_id, start, end, " sc-clear")}>{self.overlay(shot_id, shot, start, end)}</div>')

    def article(self, shot_id, shot, start, end, number, folder: Path):
        page = json.loads((folder / "assets" / shot["src"]).with_suffix(".json").read_text(encoding="utf-8"))
        view = shot["view"]
        scale = round(1920 / view["width"], 4)
        marks = []
        for index, mark in enumerate(shot.get("marks", [])):
            boxes = page["phrases"].get(mark["phrase"])
            if not boxes:
                sys.exit(f'visuals.json: "{mark["phrase"]}" was not located on {shot["src"]}: re-run screenshot.py with it')
            moment = self.section.when(mark["at"], advance=False) - 0.1 if "at" in mark else start + 0.4 + 0.9 * index
            for part, box_index in enumerate(mark.get("boxes", [0])):
                x, y, w, h = boxes[box_index]
                marks.append(f'<div id="{shot_id}-m{index}-{part}" class="sc-mark" style="left: {x - MARK_PAD}px; top: {y - MARK_PAD}px; '
                             f'width: {w + 2 * MARK_PAD}px; height: {h + 2 * MARK_PAD}px"></div>')
                self.js.append(f'sweep("#{shot_id}-m{index}-{part}", {self.local(min(max(moment, start + 0.2), end - 0.7) + 0.45 * part)});')
        size = f'width: {page["width"]}px; height: {page["height"]}px'
        source = f'<div class="sc-source" data-layout-allow-occlusion>{rich(shot["source"])}</div>' if shot.get("source") else ""
        self.html.append(
            f'<div {self.clip(shot_id, start, end, " sc-paper")}><div id="{shot_id}-pan" class="sc-pan" data-layout-allow-overflow>'
            f'<div class="sc-page" style="{size}; transform: scale({scale}) translate(-{view["x"]}px, -{view["y"]}px)">'
            f'<img src="assets/{shot["src"]}" alt="" style="{size}" />{"".join(marks)}</div></div>{source}</div>')
        self.js.append(f'drift("#{shot_id}-pan", {self.local(start)}, {round(end - start, 3)}, {-round(shot.get("pan", 35) * scale)});')

    def tiles(self, shot_id, shot, start, end, number):
        tiles = shot["tiles"]
        left = (1920 - (len(tiles) * 400 + (len(tiles) - 1) * 32)) / 2
        rows = [f'<div class="sc-title"><span id="{shot_id}-title">{rich(shot["title"])}</span></div>']
        self.js.append(f'land("#{shot_id}-title", {self.local(start + 0.1)});')
        for index, tile in enumerate(tiles):
            body = f'<div class="t">{rich(tile)}</div>' if tile else '<div class="q">?</div>'
            rows.append(f'<div id="{shot_id}-tile{index}" class="sc-tile" style="left: {left + index * 432}px">'
                        f'<div class="n">{index + 1}</div>{body}</div>')
            self.js.append(f'pop("#{shot_id}-tile{index}", {self.local(start + 0.45 + 0.3 * index)});')
        self.html.append(f'<div {self.clip(shot_id, start, end)}>{"".join(rows)}</div>')

    def number(self, shot_id, shot, start, end, number):
        lines = [{"text": shot["value"], **({"at": shot["at_value"]} if "at_value" in shot else {})}] + shot.get("text", [])
        times = self.line_times(lines, start, end)
        # The number always lands first; a label with no phrase of its own follows it.
        for index, line in enumerate(lines[1:], start=1):
            if "at" not in line:
                times[index] = round(max(times[index], times[0] + 0.3 + 0.45 * (index - 1)), 3)
        # The hero number shrinks as it gets longer, so it always fits on one line.
        size = next(px for limit, px in ((5, 300), (8, 230), (11, 170), (99, 120)) if len(shot["value"]) <= limit)
        rows = [f'<div id="{shot_id}-v" class="sc-hero" style="font-size: {size}px">{rich(shot["value"])}</div><div class="sc-rule"></div>']
        self.js.append(f'pop("#{shot_id}-v", {times[0]});')
        for index, line in enumerate(shot.get("text", [])):
            rows.append(f'<div id="{shot_id}-t{index}" class="sc-{line.get("style", "text")}">{rich(line["text"])}</div>')
            self.js.append(f'land("#{shot_id}-t{index}", {times[index + 1]});')
        note = f'<div class="sc-note">{rich(shot["note"])}</div>' if shot.get("note") else ""
        self.html.append(f'<div {self.clip(shot_id, start, end)}><div class="sc-center">{"".join(rows)}</div>{note}</div>')

    def statement(self, shot_id, shot, start, end, number):
        lines = shot["text"]
        rows = []
        for index, moment in enumerate(self.line_times(lines, start, end)):
            rows.append(f'<div id="{shot_id}-t{index}" class="sc-{lines[index].get("style", "statement")}">{rich(lines[index]["text"])}</div>')
            self.js.append(f'land("#{shot_id}-t{index}", {moment});')
        self.html.append(f'<div {self.clip(shot_id, start, end)}><div class="sc-center">{"".join(rows)}</div></div>')

    def bars(self, shot_id, shot, start, end, number):
        bars, tallest = shot["bars"], max(bar["value"] for bar in shot["bars"])
        spacing = 560
        left = (1920 - (len(bars) - 1) * spacing) / 2
        title = f'<div class="sc-title"><span id="{shot_id}-title">{rich(shot["title"])}</span></div>'
        self.js.append(f'land("#{shot_id}-title", {self.local(start + 0.1)});')
        rows = []
        for index, bar in enumerate(bars):
            height = round(300 * bar["value"] / tallest)
            centre = left + index * spacing
            moment = self.local((self.section.when(bar["at"], advance=False) - 0.1) if "at" in bar else start + 0.5 + 0.8 * index)
            rows.append(f'<div id="{shot_id}-b{index}" class="sc-bar{" strong" if bar.get("strong") else ""}" '
                        f'style="left: {centre - 160}px; height: {height}px"></div>'
                        f'<div id="{shot_id}-bv{index}" class="sc-bar-value" style="left: {centre - 240}px; bottom: {height + 84}px">{rich(bar["display"])}</div>'
                        f'<div class="sc-bar-label" style="left: {centre - 240}px">{rich(bar["label"])}</div>')
            self.js.append(f'grow("#{shot_id}-b{index}", {moment});')
            self.js.append(f'land("#{shot_id}-bv{index}", {round(moment + 0.35, 3)});')
        if shot.get("delta"):
            moment = self.local((self.section.when(shot["delta_at"], advance=False) - 0.1) if "delta_at" in shot else end - 2)
            title += f'<div id="{shot_id}-delta" class="sc-delta">{rich(shot["delta"])}</div>'
            self.js.append(f'pop("#{shot_id}-delta", {moment});')
        note = f'<div class="sc-note">{rich(shot["note"])}</div>' if shot.get("note") else ""
        self.html.append(f'<div {self.clip(shot_id, start, end)}>{title}<div class="sc-bars">{"".join(rows)}</div>{note}</div>')


def build_section(folder: Path, section: Section, shots: list[dict]) -> None:
    scene = Scene(section)
    # Each shot's phrase is searched after the previous shot's, and its text lines are searched from its own start.
    starts, cursors = [section.start], [0]
    for shot in shots[1:]:
        starts.append(max(section.when(shot["at"]) - LEAD_S, section.start))
        cursors.append(section.cursor)
    for number, shot in enumerate(shots):
        start = starts[number]
        section.cursor = cursors[number]
        end = starts[number + 1] if number + 1 < len(shots) else section.end
        if end - start < MIN_SHOT_S:
            sys.exit(f'visuals.json: the shot at "{shot.get("at")}" in {section.id} lasts {end - start:.1f}s; merge it with a neighbour')
        if end - start > LONG_SHOT_S:
            print(f'  WARNING {section.id}: the shot at "{shot.get("at", "start")}" lasts {end - start:.1f}s; add a shot inside it')
        shot_id = f"{section.id}-k{number}"
        builder = getattr(scene, shot["type"], None)
        if builder is None:
            sys.exit(f'visuals.json: unknown shot type "{shot["type"]}"')
        if shot["type"] == "article":
            builder(shot_id, shot, start, end, number, folder)
        else:
            builder(shot_id, shot, start, end, number)
    body = "\n    ".join(scene.html)
    script = "\n    ".join(scene.js)
    (folder / "compositions" / f"{section.id}.html").write_text(
        f'<template>\n  <style>{STYLE}  </style>\n  <div id="root" data-composition-id="{section.id}" data-width="1920" data-height="1080">\n'
        f'    {body}\n  </div>\n  <script>{SCRIPT_HEAD}\n    {script}\n    window.__timelines["{section.id}"] = tl;\n  </script>\n</template>\n',
        encoding="utf-8")
    print(f"{section.id}: {len(shots)} shots, one every {(section.end - section.start) / len(shots):.1f}s")


def host(name: str, start: float, duration: float, layer: int, kind: str = "graphics") -> str:
    return (f'      <div id="{name}" data-composition-id="{name}" data-composition-src="compositions/{name}.html" data-start="{round(start, 3)}" '
            f'data-duration="{round(duration, 3)}" data-track-index="{layer}" data-track-kind="{kind}" data-width="1920" data-height="1080" '
            f'style="z-index: {layer}"></div>')


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    visuals = json.loads((folder / "visuals.json").read_text(encoding="utf-8"))
    spans = json.loads((folder / "sections.json").read_text(encoding="utf-8"))
    aligned = json.loads((folder / "aligned.json").read_text(encoding="utf-8"))
    total = spans[-1]["end"]
    (folder / "compositions").mkdir(exist_ok=True)

    hosts = []
    for span in spans:
        if not span["narrated"]:
            (folder / "compositions" / "intro.html").write_text((TEMPLATES / "intro.html").read_text(encoding="utf-8"), encoding="utf-8")
            hosts.append(host("intro", span["start"], span["end"] - span["start"], 1))
            continue
        shots = visuals["sections"].get(span["id"])
        if not shots:
            sys.exit(f'visuals.json has no shots for section {span["id"]}')
        build_section(folder, Section(span, [w for w in aligned if w["section"] == span["id"]]), shots)
        hosts.append(host(span["id"], span["start"], span["end"] - span["start"], 1))

    (folder / "compositions" / "particles.html").write_text(
        (TEMPLATES / "particles.html").read_text(encoding="utf-8").replace("__LENGTH__", str(round(total, 2))), encoding="utf-8")
    hosts.append(host("particles", 0, total, 5))
    hosts.append(host("captions", 0, total, 6, "captions"))

    if not (folder / "assets" / "audio" / "mix.wav").exists():
        sys.exit("assets/audio/mix.wav is missing: run mix_audio.py first")
    tracks = [f'      <audio id="mix" class="clip" src="assets/audio/mix.wav" data-start="0" data-duration="{round(total, 3)}" '
              f'data-track-index="7" data-volume="1"></audio>']

    (folder / "index.html").write_text(f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #000000; }}
      #root {{ width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{round(total, 3)}" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
{chr(10).join(tracks)}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""", encoding="utf-8")
    print(f"index.html: {total:.1f}s, {len(hosts)} scenes")


if __name__ == "__main__":
    main()

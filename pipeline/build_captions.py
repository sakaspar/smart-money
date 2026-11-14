"""Build the captions scene from the timed script.

  build_captions.py <video_dir>

Reads aligned.json (from align.py) and writes compositions/captions.html. The narration is shown at the
bottom of the screen in short groups, one at a time, and each word brightens as it is spoken, so TV
viewers can follow along.
"""
import html
import json
import sys
from pathlib import Path

MAX_WORDS = 5
PAUSE_BREAK_S = 0.4      # a silence this long always starts a new group
LEAD_S = 0.05            # a group appears just before its first word
TAIL_S = 0.3             # and stays this long after its last word, unless the next group starts
FIRST_START_S = 0.12     # a caption at exactly 0 s looks like it was already there
FONT_PX = 58

TEMPLATE = """<template>
  <style>
    #root {{
      position: absolute;
      inset: 0;
      font-family: "Inter", sans-serif;
    }}
    .cap-group {{
      position: absolute;
      left: 0;
      bottom: 78px;
      width: 1920px;
      text-align: center;
    }}
    .cap-box {{
      display: inline-block;
      padding: 14px 34px 16px;
      border-radius: 14px;
      background: rgba(0, 0, 0, 0.8);
      color: #f4eedd;
      font-size: {font}px;
      font-weight: 700;
      line-height: 1.15;
      white-space: nowrap;
    }}
    .cap-w {{
      display: inline-block;
    }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
{groups}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    const spoken = {spoken};
    spoken.forEach(([id, at]) => tl.fromTo("#" + id, {{ opacity: 0.5 }}, {{ opacity: 1, duration: 0.12, ease: "power2.out" }}, at));
    window.__timelines["captions"] = tl;
  </script>
</template>
"""


def group_words(words: list[dict]) -> list[list[dict]]:
    groups: list[list[dict]] = [[]]
    for index, word in enumerate(words):
        groups[-1].append(word)
        if index + 1 == len(words):
            break
        following = words[index + 1]
        new_paragraph = (following["section"], following["paragraph"]) != (word["section"], word["paragraph"])
        sentence_end = word["word"][-1] in ".?!"
        clause_end = word["word"][-1] in ",;:" and len(groups[-1]) >= 3
        long_pause = following["start"] - word["end"] >= PAUSE_BREAK_S
        if new_paragraph or sentence_end or clause_end or long_pause or len(groups[-1]) == MAX_WORDS:
            groups.append([])
    return [group for group in groups if group]


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    groups = group_words(json.loads((folder / "aligned.json").read_text(encoding="utf-8")))
    blocks, spoken, counter = [], [], 0
    for index, group in enumerate(groups):
        start = max(FIRST_START_S if index == 0 else 0.0, group[0]["start"] - LEAD_S)
        end = group[-1]["end"] + TAIL_S
        if index + 1 < len(groups):
            end = min(end, groups[index + 1][0]["start"] - LEAD_S)
        end = max(end, start + 0.2)
        spans = []
        for word in group:
            word_id = f"cap-w{counter}"
            counter += 1
            spans.append(f'<span id="{word_id}" class="cap-w">{html.escape(word["word"])}</span>')
            spoken.append([word_id, round(max(start, word["start"]), 3)])
        blocks.append(
            f'    <div id="cap-g{index}" class="cap-group clip" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
            f'data-track-index="1"><span class="cap-box">{" ".join(spans)}</span></div>')
    out = folder / "compositions" / "captions.html"
    out.write_text(TEMPLATE.format(groups="\n".join(blocks), spoken=json.dumps(spoken), font=FONT_PX), encoding="utf-8")
    print(f"{len(groups)} caption groups, {counter} words -> {out}")


if __name__ == "__main__":
    main()

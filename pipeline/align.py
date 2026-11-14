"""Give every word of the script a time, so captions and shots follow the script and not the speech recogniser.

  align.py <video_dir>

Reads script.md, sections.json and words.json (from words.py). Writes aligned.json:

  [{"section": "hook", "paragraph": 0, "word": "3.6%", "start": 3.28, "end": 4.5}, ...]

Recognised words are matched to script words in order. A script word the recogniser missed or misheard
gets a time spread evenly between its matched neighbours.
"""
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

from voice import read_script


def plain(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def heard_words(raw: list[dict]) -> list[dict]:
    """Whisper splits '3.6%' into '3', '.6', '%': glue pieces without a leading letter or digit back on."""
    words: list[dict] = []
    for token in raw:
        text = token["word"].strip()
        if words and text and not re.match(r"[A-Za-z0-9$\"'(]", text):
            words[-1] = {**words[-1], "word": words[-1]["word"] + text, "end": token["end"]}
        elif text:
            words.append({"word": text, "start": token["start"], "end": token["end"]})
    return words


def align_section(script_words: list[dict], heard: list[dict], start: float, end: float) -> list[dict]:
    matcher = SequenceMatcher(a=[plain(w["word"]) for w in script_words], b=[plain(w["word"]) for w in heard], autojunk=False)
    times: list[tuple[float, float] | None] = [None] * len(script_words)
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            times[block.a + offset] = (heard[block.b + offset]["start"], heard[block.b + offset]["end"])
    index = 0
    while index < len(times):
        if times[index] is not None:
            index += 1
            continue
        gap_end = index
        while gap_end < len(times) and times[gap_end] is None:
            gap_end += 1
        left = times[index - 1][1] if index else start
        right = times[gap_end][0] if gap_end < len(times) else end
        step = (right - left) / (gap_end - index)
        for slot in range(index, gap_end):
            times[slot] = (left + step * (slot - index), left + step * (slot - index + 1))
        index = gap_end
    return [{**word, "start": round(times[i][0], 3), "end": round(times[i][1], 3)} for i, word in enumerate(script_words)]


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    heard = heard_words(json.loads((folder / "words.json").read_text(encoding="utf-8")))
    spans = {row["id"]: row for row in json.loads((folder / "sections.json").read_text(encoding="utf-8"))}
    aligned, missed = [], 0
    for section in read_script(folder / "script.md"):
        span = spans[section["id"]]
        if not span["narrated"]:
            continue
        script_words = [{"section": section["id"], "paragraph": number, "word": word}
                        for number, paragraph in enumerate(section["paragraphs"]) for word in paragraph.split()]
        inside = [w for w in heard if span["start"] - 0.2 <= w["start"] < span["end"]]
        rows = align_section(script_words, inside, span["start"], span["end"])
        missed += len(script_words) - sum(block.size for block in SequenceMatcher(
            a=[plain(w["word"]) for w in script_words], b=[plain(w["word"]) for w in inside], autojunk=False).get_matching_blocks())
        aligned += rows
    (folder / "aligned.json").write_text(json.dumps(aligned, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(aligned)} script words timed, {missed} estimated from their neighbours")


if __name__ == "__main__":
    main()

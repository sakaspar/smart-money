"""Check a script before voicing it: word count per section, and any number with no pronunciation.

  check_say.py <video_dir>

Run it after editing script.md or say.json. Voicing takes about four times the length of the speech, so
find a missing pronunciation here and not an hour into the voice step.
"""
import json
import re
import sys
from pathlib import Path

from voice import PACE, read_script


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    say = json.loads((folder / "say.json").read_text(encoding="utf-8"))
    total, missing = 0, set()
    for section in read_script(folder / "script.md"):
        text = " ".join(section["paragraphs"])
        for written in sorted(say, key=len, reverse=True):
            text = text.replace(written, say[written])
        left = set(re.findall(r"\S*[\d$%]\S*", text))
        missing |= left
        words = sum(len(p.split()) for p in section["paragraphs"])
        total += words
        print(f"{section['id']}: {words} words" + (f"  NO PRONUNCIATION: {', '.join(sorted(left))}" if left else ""))
    print(f"total: {total} words, roughly {total / 135:.0f} minutes at the body pace ({PACE['body']['speed']}x)")
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()

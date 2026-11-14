"""Write the paste-ready YouTube text for a video.

  upload_kit.py <video_dir>

Reads upload.json (titles, summary, chapter names, sources, disclaimer, tags), sections.json (chapter
times), visuals.json and assets/stock/sources.json (credits for the stock actually used). Writes youtube.txt.

YouTube's rules it checks: a title is at most 100 characters, the description at most 5,000, the tags
at most 500 characters together, the first chapter starts at 0:00 and every chapter lasts 10 seconds or more.
"""
import json
import sys
from pathlib import Path

TITLE_MAX, DESCRIPTION_MAX, TAGS_MAX, CHAPTER_MIN_S = 100, 5000, 500, 10


def clock(seconds: float) -> str:
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    kit = json.loads((folder / "upload.json").read_text(encoding="utf-8"))
    spans = json.loads((folder / "sections.json").read_text(encoding="utf-8"))
    visuals = json.loads((folder / "visuals.json").read_text(encoding="utf-8"))
    ledger = json.loads((folder / "assets" / "stock" / "sources.json").read_text(encoding="utf-8"))

    problems = [f'title over {TITLE_MAX} characters: "{title}"' for title in kit["titles"] if len(title) > TITLE_MAX]
    chapters, starts = [], []
    for span in spans:
        name = kit["chapters"].get(span["id"])
        if name:  # a section with no chapter name (the intro) stays inside the chapter before it
            chapters.append(f"{clock(span['start'])} {name}")
            starts.append(span["start"])
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else spans[-1]["end"]
        if end - start < CHAPTER_MIN_S:
            problems.append(f"chapter at {clock(start)} is shorter than {CHAPTER_MIN_S} seconds")
    if starts and starts[0] != 0:
        problems.append("the first chapter must start at 0:00")

    used = {Path(shot["src"]).name for shots in visuals["sections"].values() for shot in shots if shot.get("src", "").startswith("stock/")}
    authors = sorted({ledger[name]["author"] for name in used if ledger.get(name, {}).get("author")})
    description = "\n".join(
        kit["summary"] + ["", "CHAPTERS"] + chapters + ["", "SOURCES"] + kit["sources"]
        + ["", "Stock photos and video from Pexels, by: " + ", ".join(authors) + ".", "", kit["disclaimer"]])
    tags = ", ".join(kit["tags"])
    if len(description) > DESCRIPTION_MAX:
        problems.append(f"description is {len(description)} characters, over {DESCRIPTION_MAX}")
    if len(tags) > TAGS_MAX:
        problems.append(f"tags are {len(tags)} characters together, over {TAGS_MAX}")

    text = "\n".join(["TITLES (pick one)"] + [f"{n}. {title}" for n, title in enumerate(kit["titles"], start=1)]
                     + ["", "DESCRIPTION", description, "", "TAGS", tags, ""])
    (folder / "youtube.txt").write_text(text, encoding="utf-8")
    print(f"youtube.txt: {len(kit['titles'])} titles, {len(chapters)} chapters, description {len(description)} characters, "
          f"tags {len(tags)} characters, {len(authors)} credited authors")
    if problems:
        sys.exit("FIX: " + "; ".join(problems))


if __name__ == "__main__":
    main()

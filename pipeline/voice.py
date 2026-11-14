r"""Voice a video's script.md and lay the sections out on one timeline.

  voice.py <video_dir>

Reads script.md (sections start with "## id"; "## intro" is the silent slot for the channel intro) and
say.json (how to pronounce numbers and symbols). Writes:

  audio/<section>.raw.wav   Chatterbox output at normal speed (cached: only changed sections are re-voiced)
  assets/audio/voice.wav    the whole narration, with silence where the intro plays
  sections.json             [{"id", "start", "end", "narrated"}] in seconds

Chatterbox runs in its own Python (CHATTERBOX_PYTHON, default C:\code\2d\tools\.venv) on the GPU and copies
the narrator from voices/narrator_ref.wav. Any Python 3 can run this file; it needs ffmpeg on the PATH.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHATTERBOX_PYTHON = os.environ.get("CHATTERBOX_PYTHON", r"C:\code\2d\tools\.venv\Scripts\python.exe")
NARRATOR = ROOT / "voices" / "narrator_ref.wav"
INTRO_ID = "intro"
INTRO_S = 6.0
SECTION_TAIL_S = 0.4      # silence after a section before the next thing starts
RATE = 48000
# Final pace per kind of section: playback speed, then silence between sentences and paragraphs (seconds).
PACE = {
    "hook": {"speed": 1.05, "sentence_gap": 0.23, "paragraph_gap": 0.48},
    "body": {"speed": 0.85, "sentence_gap": 0.5, "paragraph_gap": 1.2},
}


def read_script(path: Path) -> list[dict]:
    sections: list[dict] = []
    for block in re.split(r"^## +", path.read_text(encoding="utf-8"), flags=re.M)[1:]:
        heading, _, body = block.partition("\n")
        paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        sections.append({"id": heading.strip(), "paragraphs": paragraphs})
    return sections


def spoken(text: str, say: dict[str, str]) -> str:
    for written in sorted(say, key=len, reverse=True):
        text = text.replace(written, say[written])
    leftover = re.findall(r"\S*[\d$%]\S*", text)
    if leftover:
        sys.exit(f"say.json has no pronunciation for: {', '.join(sorted(set(leftover)))}")
    return text


def seconds_of(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


def voice_section(folder: Path, section: dict, say: dict[str, str]) -> Path:
    pace = PACE["hook" if section["id"] == "hook" else "body"]
    job = {"paragraphs": [spoken(p, say) for p in section["paragraphs"]],
           "sentence_gap": round(pace["sentence_gap"] * pace["speed"], 3),
           "paragraph_gap": round(pace["paragraph_gap"] * pace["speed"], 3)}
    digest = hashlib.sha1(json.dumps(job, sort_keys=True).encode()).hexdigest()
    raw, stamp = folder / "audio" / f"{section['id']}.raw.wav", folder / "audio" / f"{section['id']}.hash"
    if raw.exists() and not stamp.exists():
        stamp.write_text(digest)  # a raw file placed here by hand is adopted as it is
    if not raw.exists() or stamp.read_text() != digest:
        jobs = folder / "audio" / f"{section['id']}.job.json"
        jobs.write_text(json.dumps([{**job, "out": str(raw)}]), encoding="utf-8")
        print(f"voicing {section['id']} ({sum(len(p.split()) for p in job['paragraphs'])} words)", flush=True)
        subprocess.run([CHATTERBOX_PYTHON, str(ROOT / "pipeline" / "chatterbox_voice.py"), str(NARRATOR), str(jobs)], check=True)
        jobs.unlink()
        stamp.write_text(digest)
    paced = folder / "audio" / f"{section['id']}.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-filter:a", f"atempo={pace['speed']}",
                    "-ar", str(RATE), "-ac", "1", str(paced)], check=True)
    return paced


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    (folder / "audio").mkdir(exist_ok=True)
    (folder / "assets" / "audio").mkdir(parents=True, exist_ok=True)
    say = json.loads((folder / "say.json").read_text(encoding="utf-8")) if (folder / "say.json").exists() else {}
    timeline, inputs, filters, clock = [], [], [], 0.0
    for section in read_script(folder / "script.md"):
        if section["id"] == INTRO_ID:
            timeline.append({"id": INTRO_ID, "start": round(clock, 3), "end": round(clock + INTRO_S, 3), "narrated": False})
            clock += INTRO_S
            continue
        paced = voice_section(folder, section, say)
        length = seconds_of(paced)
        end = clock + length + SECTION_TAIL_S
        filters.append(f"[{len(inputs)}:a]adelay={int(clock * 1000)}[a{len(inputs)}]")
        inputs.append(paced)
        timeline.append({"id": section["id"], "start": round(clock, 3), "end": round(end, 3), "narrated": True})
        clock = end
    command = ["ffmpeg", "-y", "-v", "error"]
    for path in inputs:
        command += ["-i", str(path)]
    mix = "".join(f"[a{i}]" for i in range(len(inputs)))
    command += ["-filter_complex", ";".join(filters) + f";{mix}amix=inputs={len(inputs)}:normalize=0,apad=whole_dur={clock}[out]",
                "-map", "[out]", "-ar", str(RATE), "-ac", "1", str(folder / "assets" / "audio" / "voice.wav")]
    subprocess.run(command, check=True)
    (folder / "sections.json").write_text(json.dumps(timeline, indent=1), encoding="utf-8")
    for row in timeline:
        print(f"{row['id']}: {row['start']:.1f}s - {row['end']:.1f}s")


if __name__ == "__main__":
    main()

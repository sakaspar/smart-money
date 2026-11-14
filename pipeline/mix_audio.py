r"""Mix the narration, the music and the intro chime into one track.

  mix_audio.py <video_dir>

Reads assets/audio/voice.wav, sections.json and the "music" file named in visuals.json. Writes
assets/audio/mix.wav, the only audio track the video uses.

What it does, so the narrator is always easy to hear on TV speakers:
  - compresses the voice, so quiet words and loud words come out at a steadier level;
  - cuts the music's mid-range (500 Hz to 2 kHz), where a voice sits;
  - sets the music MUSIC_BELOW_VOICE_DB under the voice's peak level;
  - ducks the music further whenever the narrator speaks, and lets it come back in the gaps.

Any Python 3 can run this file; it needs ffmpeg on the PATH.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUSIC_BELOW_VOICE_DB = 25      # the agreed range is 20 to 30
CHIME_AT_S = 1.9               # into the intro, where the title lands
CHIME_BELOW_VOICE_DB = 6
VOICE_CHAIN = "acompressor=threshold=-20dB:ratio=3:attack=5:release=150:makeup=3,alimiter=limit=0.89:level=disabled"
MUSIC_EQ = "equalizer=f=1000:width_type=o:width=2:g=-9"
DUCK = "sidechaincompress=threshold=0.02:ratio=8:attack=15:release=500"


def peak_db(path: Path, chain: str = "anull") -> float:
    """Loudest sample of a file after a filter chain, in dB (0 is full scale)."""
    report = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"{chain},volumedetect", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
    found = re.search(r"max_volume: (-?[\d.]+) dB", report)
    if not found:
        sys.exit(f"Could not measure {path}")
    return float(found.group(1))


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    audio = folder / "assets" / "audio"
    spans = json.loads((folder / "sections.json").read_text(encoding="utf-8"))
    total = spans[-1]["end"]
    music = ROOT / "music" / json.loads((folder / "visuals.json").read_text(encoding="utf-8"))["music"]
    chime = ROOT / "pipeline" / "templates" / "chime.wav"
    voice = audio / "voice.wav"

    voice_peak = peak_db(voice, VOICE_CHAIN)
    music_gain = (voice_peak - MUSIC_BELOW_VOICE_DB) - peak_db(music, MUSIC_EQ)
    chime_gain = (voice_peak - CHIME_BELOW_VOICE_DB) - peak_db(chime)
    intro = next((span for span in spans if not span["narrated"]), None)

    graph = [
        f"[0:a]{VOICE_CHAIN},aformat=channel_layouts=stereo,asplit=2[voice][key]",
        f"[1:a]atrim=0:{total},{MUSIC_EQ},volume={music_gain:.2f}dB,aformat=channel_layouts=stereo,"
        f"afade=t=in:d=1,afade=t=out:st={total - 2:.2f}:d=2[bed]",
        f"[bed][key]{DUCK}[ducked]",
    ]
    mixed = "[voice][ducked]"
    if intro:
        graph.append(f"[2:a]volume={chime_gain:.2f}dB,aformat=channel_layouts=stereo,"
                     f"adelay={int((intro['start'] + CHIME_AT_S) * 1000)}:all=1[chime]")
        mixed += "[chime]"
    graph.append(f"{mixed}amix=inputs={3 if intro else 2}:normalize=0:duration=first,alimiter=limit=0.95:level=disabled[out]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voice), "-stream_loop", "-1", "-i", str(music), "-i", str(chime),
                    "-filter_complex", ";".join(graph), "-map", "[out]", "-t", str(total), "-ar", "48000",
                    str(audio / "mix.wav")], check=True)
    print(f"voice peak {voice_peak:.1f} dB, music set {MUSIC_BELOW_VOICE_DB} dB under it and ducked under speech -> {audio / 'mix.wav'}")


if __name__ == "__main__":
    main()

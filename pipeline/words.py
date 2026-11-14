"""Word timestamps for a voice file, so shots can cut on the word they show.

  words.py <voice.wav> <words.json>

Runs in a Python that has faster-whisper (C:\code\youtube\.venv). Whisper runs on the CPU: the CUDA
libraries it needs are not installed, and trying the GPU can hang.
"""
import json
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

MODEL = "small.en"


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    voice, out = sys.argv[1], sys.argv[2]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", voice, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    segments = list(model.transcribe(audio, word_timestamps=True, language="en")[0])
    words = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
             for segment in segments for w in segment.words]
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(words, handle, indent=1)
    print(f"{len(words)} words, {audio.size / 16000:.1f}s -> {out}")


if __name__ == "__main__":
    main()

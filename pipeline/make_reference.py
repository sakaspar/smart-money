"""Make a synthetic reference clip for Chatterbox to copy, using a local Kokoro voice.

  make_reference.py <kokoro_voice> <out.wav>

Runs in a Python that has kokoro-onnx (C:\code\youtube\.venv). The reference is synthetic on purpose:
the channel never copies a real person's voice.
"""
import sys
from pathlib import Path

import soundfile
from kokoro_onnx import Kokoro

MODELS = Path(r"C:\code\youtube\pipeline\py\models")
SPEED = 0.9  # slightly slow, so the copied narrator sounds calm
TEXT = (
    "Most people spend forty years earning their money, and about forty minutes deciding what to do with it "
    "once they stop working. That is not a criticism. Nobody teaches this. So let us walk through it slowly, "
    "one number at a time, and see what the rules actually say."
)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    voice, out = sys.argv[1], sys.argv[2]
    kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    samples, rate = kokoro.create(TEXT, voice=voice, speed=SPEED, lang="en-us")
    soundfile.write(out, samples, rate, subtype="PCM_16")
    print(f"{voice}: {len(samples) / rate:.1f}s -> {out}")


if __name__ == "__main__":
    main()

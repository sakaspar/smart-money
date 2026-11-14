"""Voice chapters with Chatterbox (Resemble AI), copying the narrator from a reference clip.

  chatterbox_voice.py <reference.wav> <jobs.json>

jobs.json: [{"out": "audio/ch00.wav", "paragraphs": ["...", "..."], "sentence_gap": 0.4, "paragraph_gap": 1.0}].
The two gaps are optional (seconds of silence). Writes each chapter as 24 kHz mono 16-bit.

Runs in the Python that has Chatterbox installed (C:\code\2d\tools\.venv, on the GPU). One sentence per take, seeded from its text, so an
unchanged sentence always gets the same take; a take that rambles is retried with a new seed.
"""
import json
import re
import sys
import wave
import zlib
from pathlib import Path

import numpy as np

RATE = 24000
EXAGGERATION = 0.5  # calm and warm; raise for more expression
CFG_WEIGHT = 0.5
MAX_TRIES = 3
GAP_SENTENCE_S = 0.24
GAP_PARAGRAPH_S = 0.5
SILENCE_LEVEL = 0.01
TARGET_RMS = 0.08
PEAK = 0.89
SENTENCE_END = re.compile(r"(?<=[.!?…])[\"')\]]*\s+")


def sentences_of(paragraph: str) -> list[str]:
    return [s.strip() for s in SENTENCE_END.split(re.sub(r"\s+", " ", paragraph)) if re.search(r"\w", s)]


def trim_silence(audio: np.ndarray) -> np.ndarray:
    loud = np.flatnonzero(np.abs(audio) > SILENCE_LEVEL)
    if loud.size == 0:
        raise RuntimeError("A sentence came back silent.")
    pad = int(0.03 * RATE)
    return audio[max(0, loud[0] - pad):min(audio.size, loud[-1] + pad)]


def make_speaker(reference: str):
    import torch
    from chatterbox.tts import ChatterboxTTS

    model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
    if model.sr != RATE:
        raise RuntimeError(f"Chatterbox sample rate {model.sr} != {RATE}")
    model.prepare_conditionals(reference, exaggeration=EXAGGERATION)

    def speak(text: str) -> np.ndarray:
        limit = 1.0 + 0.75 * len(text.split())  # seconds; much longer means it rambled
        audio = None
        for attempt in range(MAX_TRIES):
            torch.manual_seed(zlib.crc32(f"{text}|{attempt}".encode()))
            wav = model.generate(text, exaggeration=EXAGGERATION, cfg_weight=CFG_WEIGHT)
            audio = wav.squeeze(0).detach().cpu().numpy().astype(np.float32)
            if audio.size / RATE <= limit:
                break
            print(f"  retry {attempt + 1}: {audio.size / RATE:.1f}s for {text!r}", flush=True)
        audio = trim_silence(audio)
        rms = float(np.sqrt(np.mean(audio**2))) or 1.0
        return audio * (TARGET_RMS / rms)

    return speak


def voice_chapter(speak, paragraphs: list[str], sentence_gap: float = GAP_SENTENCE_S, paragraph_gap: float = GAP_PARAGRAPH_S) -> np.ndarray:
    pieces = []
    for paragraph in paragraphs:
        for index, sentence in enumerate(sentences_of(paragraph)):
            if pieces:
                pieces.append(np.zeros(int(RATE * (sentence_gap if index else paragraph_gap)), dtype=np.float32))
            pieces.append(speak(sentence))
    audio = np.concatenate(pieces)
    peak = float(np.max(np.abs(audio))) or 1.0
    return audio * min(1.0, PEAK / peak)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    reference, jobs = sys.argv[1], json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    speak = make_speaker(reference)
    for job in jobs:
        print(f"chatterbox: {Path(job['out']).name} ({len(job['paragraphs'])} paragraphs)", flush=True)
        audio = voice_chapter(speak, job["paragraphs"], job.get("sentence_gap", GAP_SENTENCE_S), job.get("paragraph_gap", GAP_PARAGRAPH_S))
        with wave.open(job["out"], "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(RATE)
            out.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    main()

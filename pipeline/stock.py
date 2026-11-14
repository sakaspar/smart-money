"""Find stock photos or video clips on Pexels (free to use, no credit required; credits are still recorded).

  stock.py photo "<search words>" <out_folder> [count]
  stock.py video "<search words>" <out_folder> [count]

Photos are saved as <slug>-<n>.jpg at 2560 px wide. Video clips are saved as <slug>-<n>.mp4, cut to the
first CLIP_SECONDS, 1920x1080 at 30 fps with no sound, plus <slug>-<n>.preview.jpg to judge the clip
without playing it. Each file's author and page go into <out_folder>/sources.json for the upload kit.

The key is read from the `pexel-api` line of the .env file in the repo root. Needs ffmpeg for video.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import requests

PHOTO_API = "https://api.pexels.com/v1/search"
VIDEO_API = "https://api.pexels.com/videos/search"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
KEY_NAME = "pexel-api"
PHOTO_WIDTH = 2560
CLIP_SECONDS = 10
MIN_CLIP_SECONDS = 6
FRAME = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30"


def api_key() -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == KEY_NAME and value.strip():
                return value.strip().strip("\"'")
    sys.exit(f"No {KEY_NAME} line found in {ENV_FILE}")


def search(api: str, query: str, count: int) -> dict:
    response = requests.get(api, headers={"Authorization": api_key()}, timeout=30,
                            params={"query": query, "orientation": "landscape", "size": "large", "per_page": count})
    if response.status_code in (401, 403):
        sys.exit("Pexels refused the key: check the pexel-api line in .env")
    response.raise_for_status()
    return response.json()


def save_photos(query: str, slug: str, folder: Path, count: int) -> dict:
    found = {}
    for index, photo in enumerate(search(PHOTO_API, query, count).get("photos", []), start=1):
        name = f"{slug}-{index}.jpg"
        image = requests.get(photo["src"]["original"], timeout=90,
                             params={"auto": "compress", "cs": "tinysrgb", "w": PHOTO_WIDTH, "fm": "jpg"})
        image.raise_for_status()
        (folder / name).write_bytes(image.content)
        found[name] = {"source": "Pexels", "author": photo.get("photographer"), "page": photo.get("url"),
                       "description": photo.get("alt")}
        print(f"{name}: {photo.get('alt')!r} by {photo.get('photographer')}")
    return found


def best_file(video: dict) -> dict | None:
    """The smallest file that is at least 1920 wide, else the widest one there is."""
    files = [f for f in video.get("video_files", []) if f.get("width") and f.get("link")]
    wide = sorted((f for f in files if f["width"] >= 1920), key=lambda f: f["width"])
    return wide[0] if wide else max(files, key=lambda f: f["width"], default=None)


def save_videos(query: str, slug: str, folder: Path, count: int) -> dict:
    found, index = {}, 0
    for video in search(VIDEO_API, query, count * 2).get("videos", []):
        source = best_file(video)
        if index == count or source is None or video.get("duration", 0) < MIN_CLIP_SECONDS:
            continue
        index += 1
        name, raw = f"{slug}-{index}.mp4", folder / f"{slug}-{index}.download.mp4"
        raw.write_bytes(requests.get(source["link"], timeout=180).content)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-t", str(CLIP_SECONDS), "-an", "-vf", FRAME,
                        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(folder / name)], check=True)
        raw.unlink()
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "2", "-i", str(folder / name), "-frames:v", "1",
                        str(folder / f"{slug}-{index}.preview.jpg")], check=True)
        found[name] = {"source": "Pexels", "author": (video.get("user") or {}).get("name"), "page": video.get("url"),
                       "seconds": min(CLIP_SECONDS, video.get("duration", 0))}
        print(f"{name}: {video.get('duration')}s by {found[name]['author']} {video.get('url')}")
    return found


def main() -> None:
    if len(sys.argv) < 4 or sys.argv[1] not in ("photo", "video"):
        sys.exit(__doc__)
    kind, query, folder = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    found = (save_photos if kind == "photo" else save_videos)(query, slug, folder, count)
    if not found:
        sys.exit(f"No {kind} found for {query!r}")
    ledger_path = folder / "sources.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
    ledger_path.write_text(json.dumps(ledger | found, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

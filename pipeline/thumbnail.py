r"""Render a video's thumbnail.html to thumbnail.jpg (1280x720, under YouTube's 2 MB limit).

  thumbnail.py <video_dir>

Runs in a Python that has Playwright and Pillow (C:\code\youtube\.venv). thumbnail.html is a plain page
1280x720 in size: one photo, three or four huge words, readable at the size of a phone thumbnail.
"""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

MAX_BYTES = 2_000_000


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1]).resolve()
    png, jpg = folder / "thumbnail.png", folder / "thumbnail.jpg"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto((folder / "thumbnail.html").as_uri())
        page.wait_for_timeout(500)
        page.screenshot(path=str(png))
        browser.close()
    Image.open(png).convert("RGB").save(jpg, quality=90)
    png.unlink()
    if jpg.stat().st_size > MAX_BYTES:
        sys.exit(f"{jpg} is over 2 MB: lower the quality")
    print(f"saved {jpg} ({jpg.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

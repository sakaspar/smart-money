"""Screenshot a real web page and locate phrases on it, so the video can highlight them as they are spoken.

  screenshot.py <url> <out.png> ["phrase" ...]

Runs in a Python that has Playwright (C:\\code\\youtube\\.venv). Saves the whole page at 2400 px wide and
writes <out>.json next to it:

  {"width": 2400, "height": 5200, "phrases": {"3.6 percent": [[x, y, w, h], ...]}}

Each box is in image pixels, one per line of text per occurrence, in page order. Nothing is drawn on the
screenshot: the scene animates the highlight over these boxes.

The browser identifies itself honestly as headless Chromium. A site that refuses automated visitors
(ssa.gov does) is reported as BLOCKED and skipped. The script also exits with an error when a phrase is
not on the page, so a wrong quote never reaches the video.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SCALE = 1.5
VIEWPORT = {"width": 1600, "height": 900}
BLOCKED = re.compile(r"access (is )?(temporarily )?(denied|restricted)|unusual activity|forbidden|just a moment|are you a robot|not a robot|verify you are human|flagged as potentially automated|complete the captcha", re.I)

BOXES_JS = """
(phrase) => {
  const wanted = phrase.toLowerCase();
  const boxes = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (!node.parentElement || !node.parentElement.offsetParent) continue;
    const text = node.textContent.toLowerCase();
    for (let at = text.indexOf(wanted); at >= 0; at = text.indexOf(wanted, at + wanted.length)) {
      const range = document.createRange();
      range.setStart(node, at);
      range.setEnd(node, at + wanted.length);
      for (const rect of range.getClientRects()) {
        if (rect.width > 1 && rect.height > 1) boxes.push([rect.left + scrollX, rect.top + scrollY, rect.width, rect.height]);
      }
    }
  }
  return boxes;
}
"""


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    url, out, phrases = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=SCALE)
        response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3000)
        refused = response is not None and response.status in (401, 403, 429)
        if refused or BLOCKED.search(page.title()) or BLOCKED.search(page.inner_text("body")[:600]):
            browser.close()
            sys.exit(f"BLOCKED by the site, skipped: {url}")
        found = {}
        for phrase in phrases:
            boxes = page.evaluate(BOXES_JS, phrase)
            if not boxes:
                browser.close()
                sys.exit(f"PHRASE NOT FOUND on {url}: {phrase!r}")
            found[phrase] = [[round(value * SCALE) for value in box] for box in boxes]
        page.screenshot(path=str(out), full_page=True)
        size = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight]")
        browser.close()
    out.with_suffix(".json").write_text(
        json.dumps({"url": url, "width": round(size[0] * SCALE), "height": round(size[1] * SCALE), "phrases": found}, indent=1),
        encoding="utf-8")
    print(f"saved {out} with {sum(len(boxes) for boxes in found.values())} highlight boxes")


if __name__ == "__main__":
    main()

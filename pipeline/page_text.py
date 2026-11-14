r"""Save the readable text of a web page, so facts are checked against the page itself and not a summary.

  page_text.py <url> <out.txt>

Runs in a Python that has Playwright (C:\code\youtube\.venv). The browser identifies itself honestly;
a site that refuses automated visitors is reported as BLOCKED and skipped.
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BLOCKED = re.compile(r"access (is )?(temporarily )?(denied|restricted)|unusual activity|forbidden|just a moment|are you a robot|not a robot|verify you are human|flagged as potentially automated|complete the captcha", re.I)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    url, out = sys.argv[1], Path(sys.argv[2])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)
        text = page.inner_text("body")
        browser.close()
    if (response is not None and response.status in (401, 403, 429)) or BLOCKED.search(text[:600]):
        sys.exit(f"BLOCKED by the site, skipped: {url}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"SOURCE: {url}\n\n{text}", encoding="utf-8")
    print(f"saved {len(text.split())} words -> {out}")


if __name__ == "__main__":
    main()

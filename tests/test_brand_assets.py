from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_website_wordmark_uses_one_text_element() -> None:
    html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "website" / "styles.css").read_text(encoding="utf-8")

    wordmark = '<span class="wordmark" aria-hidden="true">skrivi</span>'
    assert html.count(wordmark) == 2
    assert "wordmark-base" not in html
    assert "wordmark-i" not in html
    assert ".wordmark::after" in css

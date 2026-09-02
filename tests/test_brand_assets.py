from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_website_wordmark_uses_one_vector_asset() -> None:
    html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "website" / "styles.css").read_text(encoding="utf-8")
    svg = (ROOT / "website" / "assets" / "skrivi-wordmark.svg").read_text(
        encoding="utf-8"
    )

    wordmark = '<img class="wordmark" src="assets/skrivi-wordmark.svg" alt="">'
    assert html.count(wordmark) == 2
    assert ".wordmark::before" not in css
    assert ".wordmark::after" not in css
    assert "<text" not in svg
    assert '<circle cx="209.42" cy="42.06" r="8.2" fill="#f05a24"/>' in svg
    assert svg.count('stroke="#f05a24"') == 1

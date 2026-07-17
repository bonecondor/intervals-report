#!/usr/bin/env python3
"""build — renders posts/ to a static site in docs/. No dependencies.

A post is a file named by the UTC second it was published
(posts/2026-07-15T21-36-42.txt); its body is rendered verbatim. Posts are
append-only and newest-first. The build never rewrites a timestamp.
Run it with:  python3 build.py
"""

import html
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
SITE_DIR = ROOT / "docs"  # GitHub Pages serves from /docs on the main branch
STYLE_SRC = ROOT / "style.css"

DOMAIN = "intervals.report"

_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$")


def parse_post(path: Path) -> dict | None:
    if not _NAME.match(path.stem):
        return None
    return {
        "moment": datetime.strptime(path.stem, "%Y-%m-%dT%H-%M-%S"),
        "body": path.read_text().rstrip("\n"),
    }


def post_article(post: dict) -> str:
    stamp = post["moment"].strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        '<article class="post">\n'
        f'<p class="stamp">{stamp}</p>\n'
        f'<p class="numbers">{html.escape(post["body"])}</p>\n'
        "</article>"
    )


def build() -> None:
    posts = sorted(
        filter(None, (parse_post(p) for p in POSTS_DIR.glob("*.txt"))),
        key=lambda p: p["moment"],
        reverse=True,
    )

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir()

    shutil.copy(STYLE_SRC, SITE_DIR / "style.css")
    (SITE_DIR / "CNAME").write_text(DOMAIN + "\n")

    feed = "\n".join(post_article(p) for p in posts)
    (SITE_DIR / "index.html").write_text(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title></title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
{feed}
</main>
<script data-goatcounter="https://intervals.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )
    print(f"built {len(posts)} post(s) → {SITE_DIR}")


if __name__ == "__main__":
    build()

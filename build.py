#!/usr/bin/env python3
"""build — renders posts/ to a static site in docs/. No dependencies.

Posts are plain text files of numbers, named by their moment:
posts/2026-07-15T03-12.txt. tick.py writes them; this renders them.
Run it with:  python3 build.py
"""

import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
SITE_DIR = ROOT / "docs"  # GitHub Pages serves from /docs on the main branch
STYLE_SRC = ROOT / "style.css"

SITE_TITLE = ""  # unnamed, for now
DOMAIN = ""      # no CNAME until there's a domain

_NAME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})$")


def parse_post(path: Path) -> dict | None:
    m = _NAME.match(path.stem)
    if not m:
        return None
    moment = datetime(*(int(g) for g in m.groups()))
    lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
    if not all(re.fullmatch(r"-?\d+", l) for l in lines):
        return None
    return {"moment": moment, "numbers": lines}


def post_article(post: dict) -> str:
    stamp = post["moment"].strftime("%Y-%m-%d %H:%M")
    numbers = "\n".join(post["numbers"])
    return (
        '<article class="post">\n'
        f'<p class="stamp">{stamp}</p>\n'
        f"<pre>{numbers}</pre>\n"
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
    if DOMAIN:
        (SITE_DIR / "CNAME").write_text(DOMAIN + "\n")

    feed = "\n".join(post_article(p) for p in posts)
    (SITE_DIR / "index.html").write_text(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SITE_TITLE}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
{feed}
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    print(f"built {len(posts)} post(s) → {SITE_DIR}")


if __name__ == "__main__":
    build()

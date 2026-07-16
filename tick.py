#!/usr/bin/env python3
"""tick — the site decides whether to post right now. No dependencies.

Run by GitHub Actions on an hourly cron (and by hand, if you want):

    python3 tick.py            # post anything scheduled in the lookback window
    python3 tick.py --force    # post right now, schedule or not

How it works:
  - Each UTC day is hashed into a seed. The seed decides how many times the
    site posts that day (possibly zero) and at which minutes.
  - Each scheduled minute is hashed into its own seed, which decides how many
    numbers appear and what they are.
  - A post is a file in posts/ named by its scheduled moment, e.g.
    posts/2026-07-15T03-12.txt — one number per line.

Everything is deterministic from the clock, so runs are idempotent: a rerun
(or a late cron) writes exactly the posts it missed and nothing twice.
"""

import hashlib
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"

# How far back a run looks for scheduled moments it may have missed. Covers
# a full day plus slack, so even a long Actions outage self-heals.
LOOKBACK = timedelta(hours=26)

# Posts per day: drawn once per day from this pool. Zero is a real option —
# some days it says nothing.
DAY_COUNTS = [0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 5, 6, 8, 11]

# Numbers per post lean short; digit lengths lean small with a long tail.
DIGIT_LENGTHS = [1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 5, 6]


def _rng(key: str) -> random.Random:
    return random.Random(int(hashlib.sha256(key.encode()).hexdigest(), 16))


def day_schedule(day) -> list[int]:
    """Minutes-after-midnight (UTC) at which this day posts."""
    rng = _rng(day.isoformat())
    count = rng.choice(DAY_COUNTS)
    return sorted(rng.sample(range(24 * 60), count))


def post_numbers(moment: datetime) -> list[int]:
    rng = _rng(moment.strftime("%Y-%m-%dT%H-%M"))
    count = max(1, min(24, 1 + int(rng.expovariate(1 / 4))))
    return [rng.randrange(10 ** rng.choice(DIGIT_LENGTHS)) for _ in range(count)]


def write_post(moment: datetime) -> bool:
    path = POSTS_DIR / f"{moment.strftime('%Y-%m-%dT%H-%M')}.txt"
    if path.exists():
        return False
    path.write_text("\n".join(str(n) for n in post_numbers(moment)) + "\n")
    print(f"posted {path.name}")
    return True


def main() -> None:
    POSTS_DIR.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    wrote = 0

    if "--force" in sys.argv:
        wrote += write_post(now.replace(second=0, microsecond=0))
    else:
        day = (now - LOOKBACK).date()
        while day <= now.date():
            midnight = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
            for minute in day_schedule(day):
                moment = midnight + timedelta(minutes=minute)
                if now - LOOKBACK <= moment <= now:
                    wrote += write_post(moment)
            day += timedelta(days=1)

    print(f"{wrote} new post(s)" if wrote else "nothing to say right now")


if __name__ == "__main__":
    main()

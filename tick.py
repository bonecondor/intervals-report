#!/usr/bin/env python3
"""tick — the site decides, live, whether to speak. No dependencies.

GitHub Actions runs this hourly. Most runs say nothing. When it does post,
everything — that it happens, when in the hour, how many posts, their values,
whether one comes out wrong — is drawn from the operating system's entropy
pool at that moment (random.SystemRandom). There is no seed and no schedule;
nothing can be precomputed, replayed, or decoded.

The one governing law: DEFORM THE FORM, NEVER ENCODE MEANING. A deformity may
mangle the shape of the numeric output in any way, but may never introduce
anything from outside the stream. There is never anything hidden to solve.

The clock is sacred. A post is a file in posts/ named by the UTC second it
was written — posts/2026-07-15T21-36-42.txt — and the body is the post,
verbatim. Files are append-only: never edited, reordered, or deleted.

    python3 tick.py            # the normal coin flip (may sleep up to an hour)
    python3 tick.py --force    # skip the flip and the big sleep; post one burst
"""

import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"

R = random.SystemRandom()

BASE_CHANCE = 0.045   # per hourly run — roughly one posting event a day, drifting
DEFORM_CHANCE = 0.045 # per post — the overwhelming majority must be ordinary
DEFORM_AGAIN = 0.30   # a deformity makes the next post in the same burst riskier


def hazard() -> float:
    """Recent speech excites; long silence deepens. Read from posts/ itself,
    so the process feeds on its own public record — no hidden state."""
    stamps = sorted(POSTS_DIR.glob("*.txt"))
    if not stamps:
        return 1.0
    last = datetime.strptime(stamps[-1].stem, "%Y-%m-%dT%H-%M-%S").replace(
        tzinfo=timezone.utc
    )
    gap = (datetime.now(timezone.utc) - last).total_seconds() / 3600
    if gap < 2:
        return 3.0
    if gap < 8:
        return 1.6
    if gap < 36:
        return 1.0
    return 0.55


# ------------------------------ normal posts ------------------------------- #

def value() -> str:
    """One number, from a deliberately wide mixed range: mostly modest, a tail
    of very large, an occasional decimal or negative."""
    mag = R.randint(0, 6) if R.random() < 0.9 else R.randint(7, 12)
    n = R.randrange(10 ** mag, 10 ** (mag + 1)) if mag else R.randrange(0, 10)
    if R.random() < 0.07:
        n = -n
    if R.random() < 0.08:
        frac = "".join(str(R.randrange(10)) for _ in range(R.randint(1, 4)))
        return f"{n}.{frac}"
    return str(n)


def normal_body() -> str:
    return " ".join(value() for _ in range(R.randint(1, 12)))


# ------------------------------- deformities ------------------------------- #
# Shape only. Every function mangles meaningless numeric output; none may
# import anything from outside the stream.

def _values(a: int, b: int) -> list[str]:
    return [value() for _ in range(R.randint(a, b))]


def d_empty() -> str:
    return ""


def d_zero() -> str:
    return "0"


def d_repeat() -> str:
    prior = sorted(POSTS_DIR.glob("*.txt"))
    if not prior:
        return d_stammer()
    return R.choice(prior).read_text().rstrip("\n")


def d_stammer() -> str:
    return " ".join([str(R.randrange(0, 100))] * R.randint(8, 70))


def d_allsame() -> str:
    return " ".join([str(R.randrange(0, 10 ** R.randint(2, 9)))] * R.randint(2, 5))


def d_double() -> str:
    vals = _values(3, 10)
    i = R.randrange(len(vals))
    vals.insert(i, vals[i])
    return " ".join(vals)


def d_sorted() -> str:
    vals = sorted(R.randrange(0, 10 ** R.randint(1, 6)) for _ in range(R.randint(5, 12)))
    if R.random() < 0.5:
        vals.reverse()
    return " ".join(map(str, vals))


def d_marathon() -> str:
    return " ".join(value() for _ in range(R.randint(60, 400)))


def d_gaps() -> str:
    return "".join(v + " " * R.randint(1, 7) for v in _values(3, 12)).rstrip()


def d_lines() -> str:
    vals = _values(4, 14)
    cuts = sorted(R.sample(range(1, len(vals)), R.randint(1, 3)))
    parts, prev = [], 0
    for c in cuts + [len(vals)]:
        parts.append(" ".join(vals[prev:c]))
        prev = c
    return "\n".join(parts)


def d_glued() -> str:
    return ",".join(_values(4, 12))


def d_stray() -> str:
    vals = _values(2, 10)
    vals.insert(R.randrange(len(vals) + 1), R.choice("|~^;:*"))
    return " ".join(vals)


def d_cutoff() -> str:
    return " ".join(_values(2, 9)) + R.choice([".", " -"])


def d_hyperdecimal() -> str:
    whole = R.randrange(0, 10 ** R.randint(1, 3))
    frac = "".join(str(R.randrange(10)) for _ in range(R.randint(9, 17)))
    vals = _values(1, 6)
    vals[R.randrange(len(vals))] = f"{whole}.{frac}"
    return " ".join(vals)


def d_pointless() -> str:
    return " ".join(
        f"{R.randrange(0, 10 ** R.randint(1, 5))}.0" for _ in range(R.randint(3, 10))
    )


def d_zeropad() -> str:
    w = R.randint(5, 9)
    return " ".join(
        str(R.randrange(0, 10 ** R.randint(0, 4))).zfill(w) for _ in range(R.randint(3, 10))
    )


def d_commas() -> str:
    vals = _values(1, 7)
    vals[R.randrange(len(vals))] = f"{R.randrange(10 ** 6, 10 ** 10):,}"
    return " ".join(vals)


def d_sci() -> str:
    vals = _values(0, 6) + [
        f"{R.randrange(1, 10)}.{R.randrange(10)}e+{R.randint(2, 19)}"
        for _ in range(R.randint(1, 3))
    ]
    R.shuffle(vals)
    return " ".join(vals)


def d_rebase() -> str:
    fmt = R.choice(["x", "b", "o"])
    return " ".join(format(R.randrange(0, 10 ** 5), fmt) for _ in range(R.randint(2, 8)))


def d_negative() -> str:
    return " ".join(f"-{R.randrange(0, 10 ** R.randint(1, 6))}" for _ in range(R.randint(3, 10)))


DEFORMS = [
    d_empty, d_zero, d_repeat, d_stammer, d_allsame, d_double, d_sorted,
    d_marathon, d_gaps, d_lines, d_glued, d_stray, d_cutoff, d_hyperdecimal,
    d_pointless, d_zeropad, d_commas, d_sci, d_rebase, d_negative,
]


# --------------------------------- posting --------------------------------- #

def burst_size() -> int:
    x = R.random()
    if x < 0.70:
        return 1
    if x < 0.86:
        return 2
    if x < 0.94:
        return 3
    return min(3 + int(R.expovariate(0.45)), 12)


def write_post(body: str) -> str:
    while True:
        now = datetime.now(timezone.utc)
        path = POSTS_DIR / f"{now.strftime('%Y-%m-%dT%H-%M-%S')}.txt"
        if not path.exists():
            break
        time.sleep(1)
    path.write_text(body + "\n" if body else "")
    return path.name


def posted_today(now: datetime) -> bool:
    return any(POSTS_DIR.glob(now.strftime("%Y-%m-%d") + "T*.txt"))


def main() -> None:
    POSTS_DIR.mkdir(exist_ok=True)
    force = "--force" in sys.argv

    if not force:
        now = datetime.now(timezone.utc)
        p = BASE_CHANCE * hazard()
        if not posted_today(now) and now.hour >= 10:
            # The daily floor: it speaks at least once a day, but never at a
            # predictable hour. A postless day's odds climb quietly through
            # the afternoon, reaching certainty by 22:00 UTC.
            p = max(p, min(1.0, ((now.hour - 9) / 13) ** 2))
        if R.random() > p:
            print("nothing")
            return
        cap = 3500.0  # anywhere in the hour, no grid
        if not posted_today(now):
            midnight = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            # a floor post must land inside the day it is rescuing
            cap = min(cap, max(30.0, (midnight - now).total_seconds() - 90))
        time.sleep(R.uniform(0, cap))

    deformed = False
    for i in range(burst_size()):
        if i:
            time.sleep(R.uniform(2, 90))
        deformed = R.random() < (DEFORM_AGAIN if deformed else DEFORM_CHANCE)
        body = R.choice(DEFORMS)() if deformed else normal_body()
        print(f"posted {write_post(body)}" + (" (deformed)" if deformed else ""))


if __name__ == "__main__":
    main()

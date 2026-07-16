# metronome (working name)

A site that posts lists of numbers at random times, as few or as many times a
day as it wants. It doesn't mean anything yet. It might never mean anything.

## how it works

- `tick.py` — GitHub Actions runs it hourly. Each UTC day is hashed into a
  seed that fixes that day's schedule: how many posts (0–11, usually 1–3) and
  at which minutes. Each scheduled minute is hashed again to fix its numbers.
  Deterministic from the clock, so reruns never double-post and missed crons
  self-heal (26h lookback).
- `build.py` — renders `posts/` to `docs/`, which GitHub Pages serves.
- `python3 tick.py --force` — make it post right now, off-schedule.

No dependencies, same as the other report sites.

## slots left open on purpose

- Site name / wordmark (page has none)
- `<title>` (`SITE_TITLE` in build.py, currently empty)
- Domain (`DOMAIN` in build.py — when set, emits CNAME; cert playbook applies)

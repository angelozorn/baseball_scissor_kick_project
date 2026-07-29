"""
Fetch batting-stance foot positions from Baseball Savant without a browser.

The batting-stance visual (https://baseballsavant.mlb.com/visuals/batting-stance)
embeds its full dataset as a `vizData` JSON array in the page HTML. This script
downloads that page, replicates the visual's own rendering math, and writes
stance_data.csv in the exact format the old Selenium scraper (extract_stance.py)
produced, so the rest of the pipeline runs unchanged.

Rendering math (from the site's batting-stance bundle):
  - Each foot glyph is placed at translate(scale_x(cx) - 10, scale_y(cy) - 30)
    where cx/cy are the mean of the bigtoe/smalltoe/heel `*_scaled` keypoints.
  - scale_x(v) = 5.2 * (54 - v) for right-side stances, 5.2 * (v - 6) for left.
  - scale_y(v) = 143 + 5.2 * v
  - Snapshot 0 = stance setup, snapshot 2 = intercept. DOM order per snapshot
    is right foot then left foot, which yields the legacy column meaning:
      x1,y1 = right foot at stance    x3,y3 = right foot at intercept
      x2,y2 = left foot at stance     x4,y4 = left foot at intercept
  - Switch hitters have one record per side; the legacy format stores the
    left-side points in x1-y4 and the right-side points in x5-y8, duplicated
    across a b<id>_l and a b<id>_r row (data_transform.py merges them to _s).

Usage:
  python fetch_stance.py --season 2026
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "stance_data.csv"

PAGE_URL = "https://baseballsavant.mlb.com/visuals/batting-stance?seasonStart={season}&seasonEnd={season}"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Constants lifted from the site's batting-stance bundle (rW, QZ, JZ, scales)
PX_PER_UNIT = 5.2
FOOT_ANCHOR_X = 10
FOOT_ANCHOR_Y = 30

KEYPOINTS = ("bigtoe", "smalltoe", "heel")
SNAPSHOT_SUFFIX = {0: "", 2: "2"}  # stance setup and intercept


def scale_x(value: float, side: str) -> float:
    if side == "R":
        return PX_PER_UNIT * (54 - value)
    return PX_PER_UNIT * (value - 6)


def scale_y(value: float) -> float:
    return 143 + PX_PER_UNIT * value


def foot_position(record: dict, foot: str, snapshot: int, side: str) -> tuple[float, float]:
    suffix = SNAPSHOT_SUFFIX[snapshot]
    cx = sum(record[f"{foot}{p}_x{suffix}_scaled"] for p in KEYPOINTS) / 3
    cy = sum(record[f"{foot}{p}_y{suffix}_scaled"] for p in KEYPOINTS) / 3
    return scale_x(cx, side) - FOOT_ANCHOR_X, scale_y(cy) - FOOT_ANCHOR_Y


def four_points(record: dict) -> list[float]:
    side = record["side"]
    points: list[float] = []
    for snapshot in (0, 2):
        for foot in ("r", "l"):
            points.extend(foot_position(record, foot, snapshot, side))
    return points


def required_keys() -> set[str]:
    keys = {"id", "name", "side", "uniqueID"}
    for foot in ("r", "l"):
        for p in KEYPOINTS:
            for suffix in SNAPSHOT_SUFFIX.values():
                keys.add(f"{foot}{p}_x{suffix}_scaled")
                keys.add(f"{foot}{p}_y{suffix}_scaled")
    return keys


def fetch_viz_data(season: int) -> list[dict]:
    url = PAGE_URL.format(season=season)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as resp:
        html = resp.read().decode("utf-8")
    match = re.search(r"vizData = (\[.*?\]);", html, re.S)
    if not match:
        raise RuntimeError(
            "Could not find embedded vizData on the batting-stance page. "
            "Savant may have changed the page structure."
        )
    return json.loads(match.group(1))


def build_rows(data: list[dict]) -> list[list]:
    missing = required_keys() - set(data[0])
    if missing:
        raise RuntimeError(
            "batting-stance vizData is missing expected fields: " + ", ".join(sorted(missing))
        )

    by_id: dict[int, dict[str, dict]] = {}
    for record in data:
        by_id.setdefault(record["id"], {})[record["side"]] = record

    rows = []
    for player_id, sides in by_id.items():
        if len(sides) == 2:  # switch hitter: left-side points then right-side points
            points = four_points(sides["L"]) + four_points(sides["R"])
            name = sides["L"]["name"]
            for side in ("l", "r"):
                rows.append([name, f"b{player_id}_{side}", *points])
        else:
            record = next(iter(sides.values()))
            rows.append([record["name"], record["uniqueID"], *four_points(record), *[""] * 8])

    rows.sort(key=lambda r: (r[0], r[1]))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch batting-stance data from Baseball Savant.")
    parser.add_argument(
        "--season",
        type=int,
        default=datetime.now().year,
        help="Season to fetch (default: current year).",
    )
    parser.add_argument(
        "--min-players",
        type=int,
        default=150,
        help="Fail if fewer than this many players are returned (guards against empty pages).",
    )
    args = parser.parse_args()

    data = fetch_viz_data(args.season)
    players = len({record["id"] for record in data})
    if players < args.min_players:
        raise RuntimeError(
            f"Stance fetch blocked: only {players} players returned for {args.season} "
            f"(minimum required: {args.min_players})."
        )

    rows = build_rows(data)
    header = ["name", "uid"] + [f"{axis}{i}" for i in range(1, 9) for axis in ("x", "y")]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"✅ Saved {len(rows)} rows ({players} players) to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()

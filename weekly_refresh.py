"""
Weekly refresh runner for in-season updates.

Usage examples:
  python weekly_refresh.py --season 2026 --source "/path/to/new_savant_data.csv"
  python weekly_refresh.py --season 2026 --source-url "https://.../savant_export.csv"

This script:
1) Updates local savant_data.csv
2) Rebuilds stance/scissor labels and merged outputs
3) Writes data_refresh_status.json for the Streamlit app
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
STATUS_PATH = BASE_DIR / "data_refresh_status.json"
SAVANT_PATH = BASE_DIR / "savant_data.csv"
DEFAULT_2026_OPENING_DAY_UTC = datetime(2026, 3, 26, tzinfo=timezone.utc)

REQUIRED_SAVANT_COLUMNS = {
    "player_name",
    "xwoba",
    "woba",
    "babip",
    "slg",
    "xslg",
    "attack_angle",
    "attack_direction",
    "swing_path_tilt",
    "hardhit_percent",
    "obp",
    "k_percent",
    "bb_percent",
    "singles",
    "doubles",
    "triples",
    "hrs",
    "bat_speed",
    "swing_length",
    "pa",
    "whiffs",
    "swings",
    "launch_angle",
    "launch_speed",
    "bip",
}


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_status(payload: dict) -> None:
    STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def validate_savant_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = sorted(REQUIRED_SAVANT_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(
            "savant_data.csv is missing required columns: " + ", ".join(missing)
        )
    return df


def read_csv_from_url(url: str) -> pd.DataFrame:
    req = Request(url, headers={"User-Agent": "scissor-project-weekly-refresh/1.0"})
    with urlopen(req) as resp:
        content = resp.read()
    return pd.read_csv(BytesIO(content))


def run_step(script_name: str, *extra_args: str) -> None:
    cmd = [sys.executable, str(BASE_DIR / script_name), *extra_args]
    result = subprocess.run(cmd, cwd=BASE_DIR, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {result.returncode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh scissor project datasets.")
    parser.add_argument(
        "--season",
        type=int,
        default=datetime.now().year,
        help="Season year for metadata (default: current year).",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Path to new savant CSV to copy into savant_data.csv",
    )
    parser.add_argument(
        "--source-url",
        type=str,
        help="URL to download latest savant CSV into savant_data.csv",
    )
    parser.add_argument(
        "--allow-preseason",
        action="store_true",
        help="Override 2026 season-start guard (not recommended for production).",
    )
    parser.add_argument(
        "--trust-source-season",
        action="store_true",
        help=(
            "Accept a datasource with no season/year/game_date column, trusting that "
            "the source query is already filtered to the requested season."
        ),
    )
    parser.add_argument(
        "--min-rows",
        type=int,
        default=1,
        help="Fail if the savant CSV has fewer than this many rows (guards against empty exports).",
    )
    parser.add_argument(
        "--skip-stance-refresh",
        action="store_true",
        help="Keep the existing stance_data.csv instead of fetching fresh stance data from Savant.",
    )
    return parser.parse_args()


def count_rows_for_season(df: pd.DataFrame, season: int) -> int | None:
    if "season" in df.columns:
        col = pd.to_numeric(df["season"], errors="coerce")
        return int((col == season).sum())
    if "year" in df.columns:
        col = pd.to_numeric(df["year"], errors="coerce")
        return int((col == season).sum())
    if "game_date" in df.columns:
        dates = pd.to_datetime(df["game_date"], errors="coerce")
        return int((dates.dt.year == season).sum())
    return None


def enforce_season_gate(
    df: pd.DataFrame,
    season: int,
    allow_preseason: bool,
    source_pins_season: bool,
) -> None:
    if season != 2026:
        return

    now = datetime.now(timezone.utc)
    if now < DEFAULT_2026_OPENING_DAY_UTC and not allow_preseason:
        raise RuntimeError(
            "2026 refresh blocked: regular season has not started yet. "
            "Keep using 2025 data until opening day."
        )

    rows_2026 = count_rows_for_season(df, 2026)
    if rows_2026 is None:
        # Aggregated Savant exports have no per-row season column; accept them
        # when the query itself is pinned to the season (hfSea= in the URL).
        if source_pins_season:
            return
        raise RuntimeError(
            "2026 refresh blocked: datasource has no `season`, `year`, or `game_date` column, "
            "so 2026 rows cannot be verified. If the source query is already filtered to "
            "2026 (e.g. hfSea=2026 in the Savant URL), pass --trust-source-season."
        )
    if rows_2026 == 0:
        raise RuntimeError(
            "2026 refresh blocked: datasource contains 0 rows for season 2026."
        )


def main() -> None:
    args = parse_args()
    started_at = datetime.now(timezone.utc)

    if args.source and args.source_url:
        raise ValueError("Use either --source or --source-url, not both.")

    if args.source:
        source_path = Path(args.source).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        savant_df = validate_savant_csv(source_path)
        source_desc = f"file:{source_path}"
    elif args.source_url:
        savant_df = read_csv_from_url(args.source_url)
        missing = sorted(REQUIRED_SAVANT_COLUMNS - set(savant_df.columns))
        if missing:
            raise ValueError(
                "Downloaded savant CSV is missing required columns: " + ", ".join(missing)
            )
        source_desc = f"url:{args.source_url}"
    else:
        if not SAVANT_PATH.exists():
            raise FileNotFoundError(
                "No savant_data.csv found. Provide --source or --source-url."
            )
        savant_df = validate_savant_csv(SAVANT_PATH)
        source_desc = "existing:savant_data.csv"

    if len(savant_df) < args.min_rows:
        raise RuntimeError(
            f"Refresh blocked: savant CSV has only {len(savant_df)} rows "
            f"(minimum required: {args.min_rows}). The source query may be empty or broken."
        )

    source_pins_season = args.trust_source_season or bool(
        args.source_url and f"hfSea={args.season}" in args.source_url
    )
    enforce_season_gate(savant_df, args.season, args.allow_preseason, source_pins_season)
    savant_df.to_csv(SAVANT_PATH, index=False)
    if not args.skip_stance_refresh:
        run_step("fetch_stance.py", "--season", str(args.season))
    run_step("data_transform.py")
    run_step("determine_scissor.py")
    run_step("merge_data.py")
    run_step("split_data.py")

    final_df = pd.read_csv(BASE_DIR / "scissor_analysis_stats.csv")
    completed_at = datetime.now(timezone.utc)

    stance_df = pd.read_csv(BASE_DIR / "stance_data.csv")
    status = {
        "season": args.season,
        "started_at_utc": started_at.isoformat(),
        "completed_at_utc": completed_at.isoformat(),
        "source": source_desc,
        "stance_source": (
            "existing:stance_data.csv"
            if args.skip_stance_refresh
            else f"savant-batting-stance-visual:{args.season}"
        ),
        "stance_rows": int(len(stance_df)),
        "savant_rows": int(len(savant_df)),
        "final_rows": int(len(final_df)),
        "final_scissor_count": int(final_df["scissor_kick_combined"].fillna(False).sum()),
        "final_non_scissor_count": int(
            len(final_df) - final_df["scissor_kick_combined"].fillna(False).sum()
        ),
        "savant_sha256": sha256_of_file(SAVANT_PATH),
    }
    write_status(status)
    print(f"Refresh complete. Status written to {STATUS_PATH.name}")


if __name__ == "__main__":
    main()

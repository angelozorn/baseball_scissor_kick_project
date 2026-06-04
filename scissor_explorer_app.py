"""
Interactive explorer: scissor vs non-scissor groups, aggregates, per-player stats, stance plot.

Run from project root:
  streamlit run scissor_explorer_app.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.patches import Polygon, Rectangle

BASE_DIR = Path(__file__).resolve().parent
REFRESH_STATUS_PATH = BASE_DIR / "data_refresh_status.json"

SCISSOR_DEFINITION = """
The scissor kick is when a batter moves his back foot away from the plate during the swing.
This move typically ends up with the front foot closer to the plate than the back foot during contact.
"""

NON_SCISSOR_DEFINITION = """
The hitter does not move the back foot away from the plate during the swing. This is the baseline group to compare against scissor-kick hitters.
"""

COORD_COLS = [f"{a}{i}" for i in range(1, 9) for a in ("x", "y")]


def apply_custom_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg-top: #ffffff;
                --bg-mid: #f8fafc;
                --bg-bottom: #f3f6fb;
                --text-main: #122033;
                --text-muted: #44556b;
                --accent-red: #cc2b3e;
                --accent-blue: #2468d6;
                --panel: rgba(255, 255, 255, 0.92);
                --panel-strong: rgba(255, 255, 255, 0.98);
                --border: rgba(33, 90, 189, 0.2);
                --shadow: 0 10px 30px rgba(16, 33, 56, 0.08);
            }

            .stApp {
                background:
                    radial-gradient(1200px 420px at 8% -8%, rgba(204, 43, 62, 0.1), transparent 60%),
                    radial-gradient(950px 450px at 92% 0%, rgba(36, 104, 214, 0.11), transparent 60%),
                    linear-gradient(180deg, var(--bg-top) 0%, var(--bg-mid) 48%, var(--bg-bottom) 100%);
                color: var(--text-main);
                font-family: "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }

            .main .block-container {
                padding-top: 1rem;
                padding-bottom: 2.4rem;
                max-width: 1220px;
            }

            h1, h2, h3 {
                color: #13263f !important;
                letter-spacing: 0.15px;
                line-height: 1.2;
                text-wrap: balance;
            }

            h1 {
                font-weight: 800;
                font-size: clamp(1.8rem, 2.6vw, 2.45rem);
                margin-bottom: 0.2rem;
            }

            h2, h3 {
                font-weight: 700;
            }

            hr {
                border: none;
                height: 1px;
                background: linear-gradient(
                    90deg,
                    transparent,
                    rgba(36, 104, 214, 0.26),
                    rgba(204, 43, 62, 0.3),
                    transparent
                );
                margin: 1.2rem 0 1.1rem;
            }

            div[data-testid="stMetric"] {
                background: linear-gradient(165deg, rgba(255, 255, 255, 0.96), rgba(247, 251, 255, 0.98));
                border: 1px solid rgba(36, 104, 214, 0.18);
                border-radius: 14px;
                padding: 0.72rem 0.8rem;
                box-shadow: 0 8px 20px rgba(16, 33, 56, 0.07);
                transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
            }

            div[data-testid="stMetric"]:hover {
                transform: translateY(-2px);
                border-color: rgba(204, 43, 62, 0.38);
                box-shadow: 0 12px 24px rgba(16, 33, 56, 0.12);
            }

            div[data-testid="stMetricLabel"] p {
                color: #5a6e85 !important;
                font-weight: 600;
            }

            div[data-testid="stMetricValue"] {
                color: #12263f !important;
                font-weight: 700;
            }

            div[data-testid="stAlert"] {
                background: linear-gradient(140deg, rgba(36, 104, 214, 0.08), rgba(204, 43, 62, 0.08));
                border: 1px solid rgba(36, 104, 214, 0.26);
                border-radius: 12px;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
            }

            div[data-testid="stExpander"] {
                background: linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.98));
                border: 1px solid rgba(36, 104, 214, 0.24);
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 20px rgba(16, 33, 56, 0.08);
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: linear-gradient(165deg, var(--panel), var(--panel-strong));
                border-radius: 14px;
                border: 1px solid rgba(36, 104, 214, 0.18);
                box-shadow: var(--shadow);
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid rgba(36, 104, 214, 0.2);
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 10px 22px rgba(16, 33, 56, 0.08);
            }

            div[data-testid="stDataFrame"] [role="grid"] {
                background: #ffffff !important;
            }

            div[data-testid="stDataFrame"] [role="columnheader"] {
                background: linear-gradient(180deg, rgba(36, 104, 214, 0.96), rgba(24, 83, 182, 0.96)) !important;
                color: #ffffff !important;
                font-weight: 700 !important;
                border-bottom: 1px solid rgba(25, 73, 158, 0.4) !important;
            }

            div[data-testid="stDataFrame"] [role="gridcell"] {
                color: #1d2f46 !important;
                border-top: 1px solid rgba(36, 104, 214, 0.12) !important;
                background: #ffffff !important;
            }

            div[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] {
                background: rgba(36, 104, 214, 0.04) !important;
            }

            div[data-testid="stButton"] button {
                background: linear-gradient(135deg, #2468d6 0%, #cc2b3e 100%);
                color: #ffffff;
                border: 1px solid rgba(36, 104, 214, 0.35);
                border-radius: 12px;
                font-weight: 700;
                letter-spacing: 0.15px;
                box-shadow: 0 10px 20px rgba(16, 33, 56, 0.14);
                transition: transform 0.16s ease, box-shadow 0.16s ease, filter 0.16s ease;
            }

            div[data-testid="stButton"] button:hover {
                transform: translateY(-1px);
                filter: brightness(1.06);
                box-shadow: 0 14px 24px rgba(16, 33, 56, 0.22);
            }

            div[data-testid="stButton"] button:focus {
                outline: none;
                box-shadow: 0 0 0 0.2rem rgba(36, 104, 214, 0.22), 0 10px 20px rgba(16, 33, 56, 0.14);
            }

            div[data-testid="stButton"] button p,
            div[data-testid="stButton"] button span {
                color: #ffffff !important;
            }

            div[role="radiogroup"] > label {
                background: linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(246, 250, 255, 0.98));
                border: 1px solid rgba(36, 104, 214, 0.2);
                border-radius: 10px;
                margin-bottom: 0.32rem;
                padding: 0.4rem 0.55rem;
                transition: border-color 0.15s ease, background 0.15s ease;
            }

            div[role="radiogroup"] > label:hover {
                border-color: rgba(204, 43, 62, 0.38);
                background: linear-gradient(160deg, rgba(255, 247, 248, 0.98), rgba(248, 251, 255, 0.98));
            }

            div[data-testid="stExpander"] summary,
            div[data-testid="stExpander"] summary p,
            div[data-testid="stExpander"] summary span {
                color: #ffffff !important;
            }

            div[data-testid="stMarkdownContainer"] p,
            div[data-testid="stCaptionContainer"],
            .stCaption {
                color: var(--text-muted) !important;
            }

            div[data-testid="stMarkdownContainer"] strong {
                color: #12263f;
            }

            div[data-testid="stToolbar"] {
                opacity: 0.85;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_player_table() -> pd.DataFrame:
    stats_path = BASE_DIR / "scissor_analysis_stats.csv"
    stance_path = BASE_DIR / "stance_data_with_scissor.csv"
    if not stats_path.exists():
        raise FileNotFoundError(f"Missing {stats_path.name} — run merge_data.py first.")
    if not stance_path.exists():
        raise FileNotFoundError(f"Missing {stance_path.name} — run determine_scissor.py first.")

    stats = pd.read_csv(stats_path)
    for dup in ("whiffs.1", "swings.1"):
        if dup in stats.columns:
            stats = stats.drop(columns=[dup])

    if stats["name"].duplicated().any():
        stats = stats.drop_duplicates(subset=["name"], keep="first")

    stance = pd.read_csv(stance_path)
    stance = stance.drop_duplicates(subset=["name"], keep="first")
    keep = ["name", "uid", *COORD_COLS]
    keep = [c for c in keep if c in stance.columns]
    stance = stance[keep]

    merged = stats.merge(stance, on="name", how="inner")
    merged["scissor_kick_combined"] = merged["scissor_kick_combined"].fillna(False).astype(bool)

    merged["ops"] = merged["obp"] + merged["slg"]
    swings = merged["swings"].replace(0, np.nan)
    merged["whiff_percent"] = (merged["whiffs"] / swings) * 100.0

    return merged


def group_label(is_scissor: bool) -> str:
    return "Scissor kick" if is_scissor else "Non-scissor"


def _parse_utc_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def render_refresh_status() -> None:
    if not REFRESH_STATUS_PATH.exists():
        st.warning(
            "No refresh metadata found yet. Run `python weekly_refresh.py --season 2026 --source ...` once "
            "to initialize automated weekly tracking."
        )
        return

    try:
        status = json.loads(REFRESH_STATUS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        st.warning("`data_refresh_status.json` exists but could not be parsed.")
        return

    completed = _parse_utc_iso(status.get("completed_at_utc"))
    if completed:
        age_days = (datetime.now(timezone.utc) - completed).days
        freshness = (
            f"Last refresh: {completed.strftime('%Y-%m-%d %H:%M UTC')} ({age_days} day(s) ago)"
        )
    else:
        freshness = "Last refresh timestamp unavailable."

    c1 = st.columns(1)[0]
    c1.metric("Season", str(status.get("season", "—")))
    st.caption(
        f"{freshness} · Source: `{status.get('source', 'unknown')}` · "
        f"Scissor: {status.get('final_scissor_count', '—')} · "
        f"Non-scissor: {status.get('final_non_scissor_count', '—')}"
    )


def aggregate_numeric(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    out = {}
    for c in cols:
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        out[f"{c}_mean"] = s.mean()
        out[f"{c}_median"] = s.median()
    return pd.Series(out)


AGG_DISPLAY = [
    ("Players", "count"),
    ("PA (mean per player)", "pa_mean"),
    ("xWOBA (mean)", "xwoba_mean"),
    ("wOBA (mean)", "woba_mean"),
    ("OBP (mean)", "obp_mean"),
    ("SLG (mean)", "slg_mean"),
    ("OPS (mean)", "ops_mean"),
    ("Whiff % (mean)", "whiff_percent_mean"),
    ("Hard-hit % (mean)", "hardhit_percent_mean"),
    ("K% (mean)", "k_percent_mean"),
    ("Bat speed (mean)", "bat_speed_mean"),
    ("Swing length (mean)", "swing_length_mean"),
]


def group_summary(df: pd.DataFrame) -> dict:
    numeric_cols = [
        "pa",
        "xwoba",
        "woba",
        "obp",
        "slg",
        "ops",
        "babip",
        "k_percent",
        "bb_percent",
        "hardhit_percent",
        "launch_angle",
        "launch_speed",
        "whiff_percent",
        "bat_speed",
        "swing_length",
        "attack_angle",
        "attack_direction",
        "swing_path_tilt",
    ]
    agg = aggregate_numeric(df, numeric_cols)
    agg["count"] = len(df)
    return agg.to_dict()


def format_metric_value(key: str, val: float | int) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    if key == "count":
        return str(int(val))
    if "percent" in key or key.startswith("k_percent") or key in ("bb_percent_mean",):
        return f"{val:.1f}%"
    if key.startswith("pa_"):
        return f"{val:.0f}"
    return f"{val:.3f}"


def batter_box_figure(player_row: pd.Series, switch_side: str | None = None) -> plt.Figure:
    uid = str(player_row["uid"])
    side = uid[-1] if len(uid) >= 1 else "?"
    name = player_row["name"]
    is_switch = bool(
        pd.notna(player_row.get("x5")) and pd.notna(player_row.get("y5"))
    )

    fig, ax = plt.subplots(figsize=(6, 7))
    ax.set_facecolor("#f7f7f7")
    title_side = "SW" if is_switch else f"{side.upper()}HH"
    if is_switch and switch_side in ("L", "R"):
        title_side = f"SW ({switch_side})"
    ax.set_title(f"{name} ({title_side})", fontsize=14)

    box_width = 300
    box_height = 330
    ax.add_patch(
        Rectangle((0, 0), box_width, box_height, edgecolor="black", fill=False, linewidth=2)
    )

    plate_w = 40
    plate_h = 30
    plate_y = box_height // 2 - plate_h // 2
    if is_switch:
        if switch_side == "R":
            plate_x = box_width + 10
        elif switch_side == "L":
            plate_x = -plate_w - 10
        else:
            plate_x = box_width // 2 - plate_w // 2
    elif side == "l":
        plate_x = -plate_w - 10
    else:
        plate_x = box_width + 10
    home_plate = [
        (plate_x, plate_y),
        (plate_x + plate_w, plate_y),
        (plate_x + plate_w, plate_y + plate_h * 0.5),
        (plate_x + plate_w / 2, plate_y + plate_h),
        (plate_x, plate_y + plate_h * 0.5),
    ]
    ax.add_patch(Polygon(home_plate, closed=True, color="lightgray", edgecolor="black"))

    coords = []
    point_range = range(1, 9)
    if is_switch and switch_side == "L":
        point_range = range(1, 5)
    elif is_switch and switch_side == "R":
        point_range = range(5, 9)

    for i in point_range:
        xc, yc = f"x{i}", f"y{i}"
        if xc in player_row.index and pd.notna(player_row[xc]) and pd.notna(player_row[yc]):
            coords.append((player_row[xc], player_row[yc], i))

    for idx, (x, y, pt_idx) in enumerate(coords):
        if is_switch:
            if pt_idx <= 2:
                color, label = "red", f"S{pt_idx} (L)"
            elif pt_idx <= 4:
                color, label = "black", f"I{pt_idx} (L)"
            elif pt_idx <= 6:
                color, label = "steelblue", f"S{pt_idx} (R)"
            else:
                color, label = "darkgreen", f"I{pt_idx} (R)"
        else:
            if idx < 2:
                color = "red"
                label = "Stance"
            elif idx < 4:
                color = "black"
                label = "Intercept"
            else:
                color = "blue"
                label = str(pt_idx)

        ax.plot(x, y, "o", color=color, markersize=10)
        ax.text(x, y - 10, label, fontsize=8, ha="center")

    ax.set_xlim(-60, box_width + 60)
    ax.set_ylim(box_height + 20, 0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    return fig


def player_stats_tables(row: pd.Series) -> None:
    basic = {
        "PA": row.get("pa"),
        "OBP": row.get("obp"),
        "SLG": row.get("slg"),
        "OPS": row.get("ops"),
        "Whiff %": row.get("whiff_percent"),
        "Singles": row.get("singles"),
        "Doubles": row.get("doubles"),
        "Triples": row.get("triples"),
        "HRs": row.get("hrs"),
        "BIP": row.get("bip"),
    }
    adv = {
        "xWOBA": row.get("xwoba"),
        "wOBA": row.get("woba"),
        "xSLG": row.get("xslg"),
        "BABIP": row.get("babip"),
        "Launch angle": row.get("launch_angle"),
        "Launch speed": row.get("launch_speed"),
        "Hard-hit %": row.get("hardhit_percent"),
        "K%": row.get("k_percent"),
        "BB%": row.get("bb_percent"),
    }
    swing = {
        "Bat speed": row.get("bat_speed"),
        "Swing length": row.get("swing_length"),
        "Attack angle": row.get("attack_angle"),
        "Attack direction": row.get("attack_direction"),
        "Swing path tilt": row.get("swing_path_tilt"),
    }

    def fmt_cell(label: str, v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "—"
        if label in ("PA", "Singles", "Doubles", "Triples", "HRs", "BIP"):
            return str(int(v))
        if label in ("Whiff %", "Hard-hit %", "K%", "BB%"):
            return f"{float(v):.1f}%"
        return f"{float(v):.3f}"

    tab_results, tab_batted, tab_swing = st.tabs(
        ["Results / usage", "Batted-ball / plate discipline", "Swing metrics"]
    )
    with tab_results:
        st.table(
            pd.DataFrame(
                {"Value": [fmt_cell(k, basic[k]) for k in basic]}, index=list(basic.keys())
            )
        )
    with tab_batted:
        st.table(
            pd.DataFrame({"Value": [fmt_cell(k, adv[k]) for k in adv]}, index=list(adv.keys()))
        )
    with tab_swing:
        st.table(
            pd.DataFrame(
                {"Value": [fmt_cell(k, swing[k]) for k in swing]}, index=list(swing.keys())
            )
        )


def main() -> None:
    st.set_page_config(page_title="Scissor kick explorer", layout="wide")
    apply_custom_styles()
    st.title("Scissor kick vs Non-scissor")
    render_refresh_status()

    try:
        players = load_player_table()
    except FileNotFoundError as e:
        st.error(str(e))
        return

    scissor_df = players[players["scissor_kick_combined"]].copy()
    non_df = players[~players["scissor_kick_combined"]].copy()
    summary_s = group_summary(scissor_df)
    summary_n = group_summary(non_df)

    st.markdown("#### Group definitions")
    st.markdown("**Scissor kick**")
    st.markdown(SCISSOR_DEFINITION)
    st.markdown("**Non-scissor**")
    st.markdown(NON_SCISSOR_DEFINITION)
    st.markdown("### Scissor Kick vs Non-Scissor stats comparison")
    st.caption("Means are **across players** in each group (not PA-weighted).")

    rows: list[dict[str, str]] = []
    for label, key in AGG_DISPLAY:
        s_raw = summary_s.get(key)
        n_raw = summary_n.get(key)

        rows.append(
            {
                "Scissor kick": format_metric_value(key, s_raw),
                "Metric": label,
                "Non-scissor": format_metric_value(key, n_raw),
            }
        )

    # Keep the dataframe styling while sizing it tall enough to show all rows.
    row_height_px = 35
    header_height_px = 38
    table_height_px = header_height_px + row_height_px * len(rows)
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
        height=table_height_px,
    )

    st.divider()
    st.markdown("### Explore a group")
    st.markdown("Pick a group, then a player")

    if "active_group_scissor" not in st.session_state:
        st.session_state.active_group_scissor = True

    g1, g2 = st.columns(2)
    with g1:
        if st.button(
            "Scissor kick group",
            use_container_width=True,
            type="primary" if st.session_state.active_group_scissor else "secondary",
        ):
            st.session_state.active_group_scissor = True
            st.rerun()
    with g2:
        if st.button(
            "Non-scissor group",
            use_container_width=True,
            type="primary" if not st.session_state.active_group_scissor else "secondary",
        ):
            st.session_state.active_group_scissor = False
            st.rerun()

    active = st.session_state.active_group_scissor
    gdf = scissor_df if active else non_df
    summ = summary_s if active else summary_n

    st.info(group_label(active))

    with st.expander("What does this group mean?", expanded=True):
        st.markdown(SCISSOR_DEFINITION if active else NON_SCISSOR_DEFINITION)

    st.markdown("#### Group aggregates")
    mc = st.columns(4)
    for i, (label, key) in enumerate(AGG_DISPLAY):
        with mc[i % 4]:
            raw = summ.get(key)
            st.metric(label, format_metric_value(key, raw) if raw is not None else "—")

    st.markdown("#### Player view")
    names = sorted(gdf["name"].astype(str).tolist())
    if not names:
        st.warning("No players found in this group.")
        return

    panel_height_px = 780
    left_col, right_col = st.columns([1, 2])
    with left_col:
        st.markdown("**Players in this group**")
        with st.container(height=panel_height_px, border=True):
            pick = st.radio(
                "Click a player name",
                names,
                index=0,
                key=f"player_drill_{'scissor' if active else 'non_scissor'}",
                label_visibility="collapsed",
            )

    row = gdf[gdf["name"] == pick].iloc[0]
    with right_col:
        with st.container(height=panel_height_px, border=True):
            st.markdown(f"### {pick}")
            st.caption(
                f"UID: {row.get('uid', '—')} · Group: **{group_label(bool(row['scissor_kick_combined']))}**"
            )

            pc1, pc2 = st.columns([1, 1])
            with pc1:
                st.markdown(
                    "**Virtual batter’s box** (stance red tones, intercept darker; switch: L vs R coloring)"
                )
                switch_side = None
                is_switch_hitter = bool(pd.notna(row.get("x5")) and pd.notna(row.get("y5")))
                if is_switch_hitter:
                    switch_side = st.radio(
                        "Switch-hitter side",
                        options=["L", "R"],
                        horizontal=True,
                        key=f"switch_side_{pick}_{'scissor' if active else 'non_scissor'}",
                    )
                fig = batter_box_figure(row, switch_side=switch_side)
                st.pyplot(fig)
                plt.close(fig)
            with pc2:
                st.markdown("**Player statistics**")
                player_stats_tables(row)


if __name__ == "__main__":
    main()

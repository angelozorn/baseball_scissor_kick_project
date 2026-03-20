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
**Scissor kick (coach view):** the hitter starts to "split" the feet during the swing.
The **back foot drifts away from the plate** while the **front foot stays closer to the plate** at contact.

In this app, that movement puts the hitter in the **Scissor kick** group.
For switch hitters, we check both sides; if either side shows it, they count as scissor.
"""

NON_SCISSOR_DEFINITION = """
**Non-scissor (coach view):** the hitter does not show that same foot split at contact.
This is the baseline group to compare against scissor-kick hitters.
"""

COORD_COLS = [f"{a}{i}" for i in range(1, 9) for a in ("x", "y")]


def apply_custom_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #081625 0%, #0f253a 45%, #132b43 100%);
                color: #e7eef7;
            }

            .main .block-container {
                padding-top: 1.3rem;
                padding-bottom: 2rem;
            }

            h1, h2, h3 {
                color: #f5f9ff !important;
                letter-spacing: 0.2px;
            }

            div[data-testid="stMetric"] {
                background: linear-gradient(145deg, rgba(17, 37, 58, 0.95), rgba(15, 31, 49, 0.95));
                border: 1px solid rgba(95, 168, 255, 0.28);
                border-radius: 14px;
                padding: 0.65rem 0.75rem;
                box-shadow: 0 8px 24px rgba(5, 12, 20, 0.25);
            }

            div[data-testid="stMetricLabel"] p {
                color: #c6d6ea !important;
                font-weight: 600;
            }

            div[data-testid="stMetricValue"] {
                color: #ffffff !important;
                font-weight: 700;
            }

            div[data-testid="stTabs"] button {
                background: rgba(22, 43, 65, 0.65);
                border: 1px solid rgba(88, 150, 226, 0.35);
                border-radius: 10px;
                margin-right: 0.3rem;
                color: #dce9f7;
            }

            div[data-testid="stTabs"] button[aria-selected="true"] {
                background: linear-gradient(90deg, rgba(35, 79, 120, 0.95), rgba(28, 112, 148, 0.95));
                border-color: rgba(110, 191, 255, 0.6);
                color: #ffffff;
            }

            div[data-testid="stAlert"] {
                background: rgba(32, 76, 114, 0.5);
                border: 1px solid rgba(108, 196, 255, 0.45);
                border-radius: 10px;
            }

            div[data-testid="stExpander"] {
                background: rgba(11, 27, 42, 0.55);
                border: 1px solid rgba(89, 154, 229, 0.32);
                border-radius: 12px;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(9, 23, 36, 0.62);
                border-radius: 14px;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid rgba(94, 160, 236, 0.24);
                border-radius: 12px;
                overflow: hidden;
            }

            div[data-testid="stMarkdownContainer"] p {
                color: #d4e2f2;
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

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Results / usage**")
        st.table(
            pd.DataFrame(
                {"Value": [fmt_cell(k, basic[k]) for k in basic]}, index=list(basic.keys())
            )
        )
    with c2:
        st.markdown("**Batted-ball / plate discipline**")
        st.table(
            pd.DataFrame({"Value": [fmt_cell(k, adv[k]) for k in adv]}, index=list(adv.keys()))
        )
    with c3:
        st.markdown("**Swing metrics**")
        st.table(
            pd.DataFrame(
                {"Value": [fmt_cell(k, swing[k]) for k in swing]}, index=list(swing.keys())
            )
        )


def main() -> None:
    st.set_page_config(page_title="Scissor kick explorer", layout="wide")
    apply_custom_styles()
    st.title("Scissor kick vs non-scissor")
    st.caption(
        "Aggregated Statcast-style metrics (means across players), definitions, and per-player stance + stats. "
        "Duplicate `name` rows in `scissor_analysis_stats.csv` keep the **first** row as ordered in the file."
    )
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

    tab_cmp, tab_drill = st.tabs(["Compare groups", "Explore a group"])

    with tab_cmp:
        st.markdown("### Side-by-side aggregates")
        st.caption("Means are **across players** in each group (not PA-weighted).")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Scissor kick")
            mcols = st.columns(3)
            for i, (label, key) in enumerate(AGG_DISPLAY[:6]):
                with mcols[i % 3]:
                    raw = summary_s.get(key)
                    st.metric(label, format_metric_value(key, raw) if raw is not None else "—")
            mcols2 = st.columns(3)
            for j, (label, key) in enumerate(AGG_DISPLAY[6:]):
                with mcols2[j % 3]:
                    raw = summary_s.get(key)
                    st.metric(label, format_metric_value(key, raw) if raw is not None else "—")
        with c2:
            st.subheader("Non-scissor")
            mcols = st.columns(3)
            for i, (label, key) in enumerate(AGG_DISPLAY[:6]):
                with mcols[i % 3]:
                    raw = summary_n.get(key)
                    st.metric(label, format_metric_value(key, raw) if raw is not None else "—")
            mcols2 = st.columns(3)
            for j, (label, key) in enumerate(AGG_DISPLAY[6:]):
                with mcols2[j % 3]:
                    raw = summary_n.get(key)
                    st.metric(label, format_metric_value(key, raw) if raw is not None else "—")

        with st.expander("Group definitions (read me)", expanded=False):
            st.markdown("#### Scissor kick")
            st.markdown(SCISSOR_DEFINITION)
            st.markdown("#### Non-scissor")
            st.markdown(NON_SCISSOR_DEFINITION)

    with tab_drill:
        st.markdown("### Pick a group, then a player")

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

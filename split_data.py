import pandas as pd

# Load the combined dataset
df = pd.read_csv("scissor_analysis_stats.csv")

# ─────────────────────────────────────────────────────────────
# 1. BASIC STATS
basic_cols = [
    "name", "scissor_kick_combined",
    "pa", "obp", "slg", "singles", "doubles", "triples", "hrs", "whiffs","swings", "bip"
]
basic_df = df[basic_cols].copy()

# Add derived per-PA fields
basic_df["singles_per_pa"] = basic_df["singles"] / basic_df["pa"]
basic_df["doubles_per_pa"] = basic_df["doubles"] / basic_df["pa"]
basic_df["triples_per_pa"] = basic_df["triples"] / basic_df["pa"]
basic_df["hrs_per_pa"]     = basic_df["hrs"] / basic_df["pa"]

basic_df["singles_per_bip"] = basic_df["singles"] / basic_df["bip"]
basic_df["doubles_per_bip"] = basic_df["doubles"] / basic_df["bip"]
basic_df["triples_per_bip"] = basic_df["triples"] / basic_df["bip"]
basic_df["hrs_per_bip"]     = basic_df["hrs"] / basic_df["bip"]

basic_df["whiff_percent"] = basic_df["whiffs"] / basic_df["swings"]
basic_df["ops"] = basic_df["obp"] + basic_df["slg"]

# Save basic stats
basic_df.to_csv("basic_stats.csv", index=False)

# ─────────────────────────────────────────────────────────────
# 2. ADVANCED STATS
advanced_cols = [
    "name", "scissor_kick_combined",
    "xwoba", "woba", "babip", "xslg",
    "launch_angle", "launch_speed",
    "hardhit_percent", "k_percent", "bb_percent"
]
advanced_df = df[advanced_cols].copy()

# Rename launch_speed → exit_velocity
advanced_df.rename(columns={"launch_speed": "exit_velocity"}, inplace=True)

# Save advanced stats
advanced_df.to_csv("advanced_stats.csv", index=False)

# ─────────────────────────────────────────────────────────────
# 3. SWING METRICS
swing_cols = [
    "name", "scissor_kick_combined",
    "bat_speed", "swing_length",
    "attack_angle", "attack_direction", "swing_path_tilt"
]
swing_df = df[swing_cols].copy()

# Save swing metrics
swing_df.to_csv("swing_metrics.csv", index=False)

print("✅ Split complete: basic_stats.csv, advanced_stats.csv, swing_metrics.csv created.")

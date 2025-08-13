import pandas as pd

# Load datasets
stance_df = pd.read_csv("stance_data_with_scissor.csv")
savant_df = pd.read_csv("savant_data.csv")

# Select and combine scissor flags
stance_subset = stance_df[["name", "scissor_kick", "scissor_kick_l", "scissor_kick_r"]].copy()
stance_subset["scissor_kick_combined"] = (
    stance_subset["scissor_kick"].fillna(False) |
    stance_subset["scissor_kick_l"].fillna(False) |
    stance_subset["scissor_kick_r"].fillna(False)
)
stance_subset = stance_subset[["name", "scissor_kick_combined"]]

# Merge on name/player_name
merged_df = savant_df.merge(
    stance_subset,
    left_on="player_name",
    right_on="name",
    how="inner"
)

# Select desired columns
selected_columns = [
    "name", "scissor_kick_combined",
    "xwoba", "woba", "babip", "slg",  "xslg",
    "attack_angle", "attack_direction", "swing_path_tilt",
    "hardhit_percent", "obp", "k_percent", "bb_percent",
    "singles", "doubles", "triples", "hrs",
    "bat_speed", "swing_length", "pa",
    "whiffs", "swings", "launch_angle", "launch_speed", "whiffs","swings", "bip"
]

final_df = merged_df[selected_columns]

# Save to CSV
final_df.to_csv("scissor_analysis_stats.csv", index=False)
print("✅ Exported to scissor_analysis_stats.csv with selected columns.")

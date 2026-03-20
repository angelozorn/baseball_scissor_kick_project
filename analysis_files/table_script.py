import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------- Function to Show Table with Matplotlib -----------------

def show_summary_table_matplotlib(summary_table, title="Summary Table"):
    fig, ax = plt.subplots(figsize=(13, 0.5 + 0.5 * len(summary_table)))
    ax.axis('off')
    tbl = ax.table(
        cellText=summary_table.values,
        rowLabels=summary_table.index,
        colLabels=[' '.join(col).strip() for col in summary_table.columns.values],
        loc='center',
        cellLoc='center'
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.2, 1.2)
    plt.title(title, fontsize=16, pad=30)
    plt.tight_layout()
    plt.show()

# ----------------- Function to Compute Summary Table ----------------------

def make_summary_table(df, fields, groups, stats, title):
    columns = pd.MultiIndex.from_product([groups, stats])
    summary_table = pd.DataFrame(index=fields, columns=columns)

    for group in groups:
        group_df = df[df['scissor_group'] == group]
        for field in fields:
            values = group_df[field].dropna()
            summary_table.loc[field, (group, "mean")] = values.mean()
            summary_table.loc[field, (group, "median")] = values.median()
            summary_table.loc[field, (group, "25th_pct")] = np.percentile(values, 25)
            summary_table.loc[field, (group, "75th_pct")] = np.percentile(values, 75)

    # Print sample sizes at the top
    print(f"\nSample sizes for {title}:")
    for group in groups:
        print(f"{group}: {len(df[df['scissor_group'] == group])}")
    print()

    print(f"\nSummary table for {title}:\n")
    print(summary_table.round(3))
    return summary_table.round(3)

# ----------------- Define Fields and Load Data ---------------------------

basic = pd.read_csv("basic_stats.csv")
adv = pd.read_csv("advanced_stats.csv")
swing = pd.read_csv("swing_metrics.csv")

for df in [basic, adv, swing]:
    df['scissor_group'] = df['scissor_kick_combined'].map({True: "Scissor", False: "Non-Scissor"})

groups = ["Scissor", "Non-Scissor"]
stats = ["mean", "median", "25th_pct", "75th_pct"]

basic_fields = [
    "obp", "slg", "ops", "whiff_percent", "singles_per_pa", "doubles_per_pa", "triples_per_pa",
    "hrs_per_pa", "singles_per_bip", "doubles_per_bip", "triples_per_bip", "hrs_per_bip"
]

adv_fields = [
    "xwoba", "woba", "xslg", "babip", "exit_velocity", "launch_angle",
    "hardhit_percent", "k_percent", "bb_percent"
]

swing_fields = [
    "bat_speed", "swing_length", "attack_angle", "attack_direction", "swing_path_tilt"
]

# ----------------- Run for All Three Data Sets ---------------------------

basic_table = make_summary_table(basic, basic_fields, groups, stats, "Basic Stats")
show_summary_table_matplotlib(basic_table, "Basic Stats Summary Table")

adv_table = make_summary_table(adv, adv_fields, groups, stats, "Advanced Stats")
show_summary_table_matplotlib(adv_table, "Advanced Stats Summary Table")

swing_table = make_summary_table(swing, swing_fields, groups, stats, "Swing Metrics")
show_summary_table_matplotlib(swing_table, "Swing Metrics Summary Table")

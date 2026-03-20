import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind, mannwhitneyu

# For pretty plots
sns.set(style="whitegrid")

# ---------- Utility Functions ----------

def print_stats(group1, group2, metric, group1_name="Scissor", group2_name="Non-Scissor"):
    m1 = np.mean(group1)
    m2 = np.mean(group2)
    s1 = np.std(group1)
    s2 = np.std(group2)
    t_stat, p_val = ttest_ind(group1, group2, nan_policy='omit')
    u_stat, p_val_u = mannwhitneyu(group1, group2, alternative='two-sided')
    effect_size = (m1 - m2) / np.sqrt((s1**2 + s2**2) / 2)  # Cohen's d
    print(f"\nMetric: {metric}")
    print(f"{group1_name}: Mean={m1:.3f}, SD={s1:.3f} | {group2_name}: Mean={m2:.3f}, SD={s2:.3f}")
    print(f"T-test: t={t_stat:.3f}, p={p_val:.3g} | MWU: U={u_stat}, p={p_val_u:.3g} | Effect size (d): {effect_size:.3f}")
    return m1, m2, t_stat, p_val, effect_size

def boxplot_by_group(df, stat, group_col, group_labels, title):
    plt.figure(figsize=(7,5))
    sns.boxplot(x=group_col, y=stat, data=df, order=group_labels)
    plt.title(title)
    plt.xlabel("Scissor Kick")
    plt.ylabel(stat.replace('_',' ').title())
    plt.show()

def hist_by_group(df, stat, group_col, group_labels, title):
    plt.figure(figsize=(7,5))
    for group in group_labels:
        subset = df[df[group_col]==group][stat].dropna()
        sns.kdeplot(subset, label=f"{group} (n={len(subset)})", fill=True, alpha=0.5)
    plt.title(title)
    plt.xlabel(stat.replace('_',' ').title())
    plt.legend()
    plt.show()

# ---------- Load Data ----------

basic = pd.read_csv("basic_stats.csv")
adv = pd.read_csv("advanced_stats.csv")
swing = pd.read_csv("swing_metrics.csv")

for df in [basic, adv, swing]:
    # Convert 'scissor_kick_combined' to readable group labels
    df['scissor_group'] = df['scissor_kick_combined'].map({True: "Scissor", False: "Non-Scissor"})

group_labels = ["Scissor", "Non-Scissor"]

# ---------- BASIC STATS ANALYSIS ----------

print("\n===== BASIC STATS =====")
basic_stats = ["obp", "slg", "ops", "whiff_percent", "singles_per_pa", "doubles_per_pa", "triples_per_pa", "hrs_per_pa", "singles_per_bip", "doubles_per_bip", "triples_per_bip", "hrs_per_bip"]
for stat in basic_stats:
    group1 = basic[basic['scissor_group'] == "Scissor"][stat].dropna()
    group2 = basic[basic['scissor_group'] == "Non-Scissor"][stat].dropna()
    print_stats(group1, group2, stat)
    boxplot_by_group(basic, stat, "scissor_group", group_labels, f"{stat.replace('_',' ').title()} by Scissor Kick")

# ---------- ADVANCED STATS ANALYSIS ----------

print("\n===== ADVANCED STATS =====")
adv_stats = ["xwoba", "woba", "xslg", "babip", "exit_velocity", "launch_angle", "hardhit_percent", "k_percent", "bb_percent"]
for stat in adv_stats:
    group1 = adv[adv['scissor_group'] == "Scissor"][stat].dropna()
    group2 = adv[adv['scissor_group'] == "Non-Scissor"][stat].dropna()
    print_stats(group1, group2, stat)
    boxplot_by_group(adv, stat, "scissor_group", group_labels, f"{stat.replace('_',' ').title()} by Scissor Kick")

# ---------- SWING METRICS ANALYSIS ----------

print("\n===== SWING METRICS =====")
swing_stats = ["bat_speed", "swing_length", "attack_angle", "attack_direction", "swing_path_tilt"]
for stat in swing_stats:
    group1 = swing[swing['scissor_group'] == "Scissor"][stat].dropna()
    group2 = swing[swing['scissor_group'] == "Non-Scissor"][stat].dropna()
    print_stats(group1, group2, stat)
    boxplot_by_group(swing, stat, "scissor_group", group_labels, f"{stat.replace('_',' ').title()} by Scissor Kick")

# ---------- EXTRA: CORRELATION & SCATTERPLOTS ----------

# Example: Relationship between bat speed and exit velocity
if 'exit_velocity' in adv.columns and 'bat_speed' in swing.columns:
    merged = pd.merge(adv[["name", "scissor_group", "exit_velocity"]], 
                      swing[["name", "bat_speed"]], on="name")
    plt.figure(figsize=(7,5))
    sns.scatterplot(x="bat_speed", y="exit_velocity", hue="scissor_group", data=merged)
    plt.title("Bat Speed vs. Exit Velocity by Scissor Group")
    plt.show()

# ---------- OPTIONAL: TABLES OF SUMMARY STATS ----------
def summary_table(df, metrics, group_col="scissor_group"):
    summary = df.groupby(group_col)[metrics].agg(['mean','std','count'])
    print("\nSummary Table:\n", summary)

print("\n===== SUMMARY TABLES =====")
print("Basic Stats:")
summary_table(basic, basic_stats)
print("Advanced Stats:")
summary_table(adv, adv_stats)
print("Swing Metrics:")
summary_table(swing, swing_stats)

import pandas as pd

# Load stance data
df = pd.read_csv("stance_data_deduplicated.csv")

# Helper function to apply scissor kick logic
def detect_scissor(front_x, back_x, stance_back_x, side, threshold=8):
    if side == 'l':
        return (
            (back_x - front_x >= threshold) and
            (back_x - stance_back_x >= threshold)
        )
    elif side == 'r':
        return (
            (front_x - back_x >= threshold) and
            (stance_back_x - back_x >= threshold)
        )
    return False

# Columns to preserve
output_rows = []

for _, row in df.iterrows():
    name = row["name"]
    uid = row["uid"]
    side = uid[-1]
    is_switch = pd.notna(row.get("x5")) and pd.notna(row.get("y5"))

    result = row.copy()

    if is_switch:
        # LEFT SIDE: x1–x4
        stance_front_x_l = row["x1"]
        stance_back_x_l = row["x2"]
        intercept_front_x_l = row["x3"]
        intercept_back_x_l = row["x4"]
        scissor_l = detect_scissor(
            intercept_front_x_l,
            intercept_back_x_l,
            stance_back_x_l,
            side='l'
        )

        # RIGHT SIDE: x5–x8
        stance_back_x_r = row["x5"]
        stance_front_x_r = row["x6"]
        intercept_back_x_r = row["x7"]
        intercept_front_x_r = row["x8"]
        scissor_r = detect_scissor(
            intercept_front_x_r,
            intercept_back_x_r,
            stance_back_x_r,
            side='r'
        )

        result["scissor_kick_l"] = scissor_l
        result["scissor_kick_r"] = scissor_r

    else:
        # Only 4 points → use side from uid
        if side == 'l':
            stance_front_x = row["x1"]
            stance_back_x = row["x2"]
            intercept_front_x = row["x3"]
            intercept_back_x = row["x4"]
        else:
            stance_back_x = row["x1"]
            stance_front_x = row["x2"]
            intercept_back_x = row["x3"]
            intercept_front_x = row["x4"]

        scissor = detect_scissor(
            intercept_front_x,
            intercept_back_x,
            stance_back_x,
            side=side
        )
        result["scissor_kick"] = scissor

    output_rows.append(result)

# Create new DataFrame
df_out = pd.DataFrame(output_rows)

# Save result
df_out.to_csv("stance_data_with_scissor.csv", index=False)
print("✅ Saved labeled data to stance_data_with_scissor.csv")

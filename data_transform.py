import pandas as pd

# Load original stance data
df = pd.read_csv("stance_data.csv")

# Keep a clean copy for processing
deduped_rows = []

# Track already-handled names
seen_names = set()

for _, row in df.iterrows():
    name = row["name"]

    if name in seen_names:
        continue  # Skip duplicate

    # Get all rows with this name
    matching_rows = df[df["name"] == name]

    if len(matching_rows) == 2:
        row1 = matching_rows.iloc[0]
        row2 = matching_rows.iloc[1]

        # Check if x/y values are identical across both rows
        coords1 = row1[[f"x{i}" for i in range(1, 9)] + [f"y{i}" for i in range(1, 9)]].values
        coords2 = row2[[f"x{i}" for i in range(1, 9)] + [f"y{i}" for i in range(1, 9)]].values

        if (coords1 == coords2).all():
            # They're identical → keep one, change uid to _s
            new_row = row1.copy()
            base_id = new_row["uid"][:-2]  # remove last "_l" or "_r"
            new_row["uid"] = f"{base_id}_s"
            deduped_rows.append(new_row)
            seen_names.add(name)
            continue

    # If not a duplicate or not identical, keep the row as-is
    deduped_rows.append(row)
    seen_names.add(name)

# Save to new CSV
df_out = pd.DataFrame(deduped_rows)
df_out.to_csv("stance_data_deduplicated.csv", index=False)
print("✅ Saved cleaned file as stance_data_deduplicated.csv")

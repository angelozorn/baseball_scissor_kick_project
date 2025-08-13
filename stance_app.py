import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import streamlit as st

# Load stance data
df = pd.read_csv("stance_data.csv")

# Sidebar player selection
st.sidebar.title("Select a Player")
player_name = st.sidebar.selectbox("Player", df["name"].unique(), index=0)

# Filter for selected player
player_row = df[df["name"] == player_name].iloc[0]
uid = player_row["uid"]
side = uid[-1]

# Set up figure
fig, ax = plt.subplots(figsize=(6, 7))
ax.set_facecolor('#f7f7f7')
ax.set_title(f"{player_name} ({side.upper()}HH)", fontsize=14)

# Draw batter's box
box_width = 300
box_height = 330
ax.add_patch(Rectangle((0, 0), box_width, box_height, edgecolor="black", fill=False, linewidth=2))

# Draw home plate
plate_w = 40
plate_h = 30
plate_y = box_height // 2 - plate_h // 2
plate_x = -plate_w - 10 if side == 'l' else box_width + 10
home_plate = [
    (plate_x, plate_y),
    (plate_x + plate_w, plate_y),
    (plate_x + plate_w, plate_y + plate_h * 0.5),
    (plate_x + plate_w / 2, plate_y + plate_h),
    (plate_x, plate_y + plate_h * 0.5)
]
ax.add_patch(Polygon(home_plate, closed=True, color="lightgray", edgecolor="black"))

# Extract foot coords and plot
coords = []
for i in range(1, 9):
    x_col = f"x{i}"
    y_col = f"y{i}"
    if pd.notna(player_row[x_col]) and pd.notna(player_row[y_col]):
        coords.append((player_row[x_col], player_row[y_col]))

for i, (x, y) in enumerate(coords):
    if i < 2:
        color = "red"
        label = "Stance"
    elif i < 4:
        color = "black"
        label = "Intercept"
    else:
        color = "blue"
        label = f"{i+1}"
    ax.plot(x, y, 'o', color=color, markersize=10)
    ax.text(x, y - 10, label, fontsize=8, ha="center")

# Format plot
ax.set_xlim(-60, box_width + 60)
ax.set_ylim(box_height + 20, 0)
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

# Show plot in Streamlit
st.pyplot(fig)

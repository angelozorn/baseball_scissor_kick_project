import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

# Load stance data CSV
df = pd.read_csv("stance_data.csv")

# Choose a player (change index to view a different player)
player_row = df.iloc[0]
name = player_row["name"]
uid = player_row["uid"]
side = uid[-1]  # 'r' or 'l'

# Extract foot coordinates
coords = []
for i in range(1, 9):
    x_col = f"x{i}"
    y_col = f"y{i}"
    if pd.notna(player_row[x_col]) and pd.notna(player_row[y_col]):
        coords.append((player_row[x_col], player_row[y_col]))

# Set up figure
plt.figure(figsize=(6, 7))
ax = plt.gca()
ax.set_facecolor('#f7f7f7')
plt.title(f"{name} ({side.upper()}HH)", fontsize=14)

# Batter's box dimensions
box_width = 300
box_height = 330

# Draw batter's box
ax.add_patch(Rectangle((0, 0), box_width, box_height, edgecolor="black", fill=False, linewidth=2))

# Home plate setup
plate_w = 40
plate_h = 30
plate_y = box_height // 2 - plate_h // 2

# Position plate left or right of box
if side == 'l':
    plate_x = -plate_w - 10  # plate on LEFT for lefty
else:
    plate_x = box_width + 10  # plate on RIGHT for righty

home_plate = [
    (plate_x, plate_y),
    (plate_x + plate_w, plate_y),
    (plate_x + plate_w, plate_y + plate_h * 0.5),
    (plate_x + plate_w / 2, plate_y + plate_h),
    (plate_x, plate_y + plate_h * 0.5)
]
ax.add_patch(Polygon(home_plate, closed=True, color="lightgray", edgecolor="black"))

# Plot feet with custom logic
for i, (x, y) in enumerate(coords):
    if i < 2:  # Stance feet
        color = "red"
        label = "Stance"
    elif i < 4:  # Intercept feet
        color = "black"
        label = "Intercept"
    else:  # Any others (like switch hitters)
        color = "blue"
        label = f"{i+1}"

    plt.plot(x, y, 'o', color=color, markersize=10)
    plt.text(x, y - 10, label, fontsize=8, ha="center")

# Set limits and hide axes
plt.xlim(-60, box_width + 60)
plt.ylim(box_height + 20, 0)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.show()

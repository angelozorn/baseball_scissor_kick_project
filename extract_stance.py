import os
import time
import csv
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load input CSV (must have columns: id, side, name)
df = pd.read_csv("batting-stance.csv")
df["side"] = df["side"].str.lower()  # Convert 'R'/'L' to 'r'/'l'

# Prepare data list
data_rows = []

# Set up Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

for i, row in df.iterrows():
    player_id = row["id"]
    side = row["side"]
    name = row["name"]
    uid = f"b{player_id}_{side}"
    url = f"https://baseballsavant.mlb.com/visuals/batting-stance?activePlayer={uid}"

    print(f"\n⏳ [{i+1}/{len(df)}] {name} → {uid}")

    try:
        driver.get(url)
        time.sleep(5)  # Give JS time to load

        soup = BeautifulSoup(driver.page_source, "html.parser")
        foot_paths = soup.find_all("g", class_="foot-path")

        if len(foot_paths) not in [4, 8]:
            print(f"⚠️ {uid} — Found {len(foot_paths)} foot-paths (expected 4 or 8)")
            continue

        row_data = [name, uid]
        for tag in foot_paths:
            transform_attr = tag.get("transform", "")
            if "translate" in transform_attr:
                start = transform_attr.find("translate(") + len("translate(")
                end = transform_attr.find(")", start)
                coords = transform_attr[start:end]
                x, y = coords.split(",")
                row_data.append(float(x.strip()))
                row_data.append(float(y.strip()))

        # Pad to ensure 16 coordinate values (8 x-y pairs)
        while len(row_data) < 2 + 16:
            row_data.append("")

        data_rows.append(row_data)
        print(f"✅ {uid} — {len(foot_paths)} foot-paths parsed")

    except Exception as e:
        print(f"❌ Error for {uid}: {e}")

# Save to CSV
output_path = "stance_data.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    header = ["name", "uid"] + [f"x{i//2 + 1}" if i % 2 == 0 else f"y{i//2 + 1}" for i in range(16)]
    writer.writerow(header)
    writer.writerows(data_rows)

driver.quit()
print(f"\n📄 Done! Saved {len(data_rows)} rows to {output_path}")

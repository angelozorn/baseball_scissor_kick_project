# GitHub Pages setup

This project deploys the Streamlit app as a static site using [Stlite](https://stlite.net/) (Streamlit in the browser via WebAssembly).

## One-time GitHub settings

1. Open the repository on GitHub: **Settings → Pages**
2. Under **Build and deployment**, set **Source** to **GitHub Actions**
3. Save

## Deploy

Every push to `main` runs `.github/workflows/deploy.yml`, which:

1. Builds `docs/index.html` with `python deploy_pages.py`
2. Publishes the `docs/` folder to GitHub Pages

You can also run the workflow manually: **Actions → Deploy to GitHub Pages → Run workflow**.

## Live URL

After the workflow succeeds (usually 2–5 minutes):

**https://angelozorn.github.io/baseball_scissor_kick_project/**

## Local preview

```bash
python deploy_pages.py
python -m http.server 8000
```

Open http://localhost:8000/docs/index.html

## Rebuild after app changes

Edit `scissor_explorer_app.py` (and data CSVs if needed), commit, and push to `main`. CI rebuilds automatically.

To preview locally before pushing:

```bash
python deploy_pages.py
```

## Weekly automated data refresh

`.github/workflows/weekly-refresh.yml` runs every Monday at 11:00 UTC, March through
November. It downloads a fresh Savant CSV, reruns the full pipeline
(`weekly_refresh.py`), commits the updated data to `main`, and redeploys GitHub Pages.

### One-time setup

1. On Baseball Savant, open your saved scissor statcast search and copy the **CSV
   export URL** (right-click the download/CSV button → Copy Link Address). It looks
   like `https://baseballsavant.mlb.com/statcast_search/csv?hfSea=2026%7C&...`
2. On GitHub: **Settings → Secrets and variables → Actions → Variables →
   New repository variable**
   - Name: `SAVANT_CSV_URL`
   - Value: the URL from step 1

The workflow automatically rewrites the `hfSea=` year in the URL to the current
season, so the variable does not need updating each year.

### Manual run

**Actions → Weekly Data Refresh → Run workflow.** Optional inputs let you override
the source URL or season for a one-off run.

### Safety guards

- The refresh fails (and nothing is published) if the download has fewer than 100
  rows or is missing required columns.
- The 2026 preseason gate in `weekly_refresh.py` still applies; a URL pinned with
  `hfSea=<season>` satisfies the season check for aggregated exports that lack a
  season column.

### Known limitation

`stance_data.csv` (batting-stance coordinates) is scraped manually with
`extract_stance.py` and is **not** refreshed by this workflow. Players who debut
after the last stance scrape will be missing stance labels and drop out of the
merged analysis until the scrape is rerun.

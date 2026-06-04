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

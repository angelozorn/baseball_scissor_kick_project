"""Build static Stlite bundle in docs/ for GitHub Pages."""

from pathlib import Path

from stlitepack import pack

BASE_PATH = "baseball_scissor_kick_project"
GITHUB_REPO = f"angelozorn/{BASE_PATH}"

DATA_FILES = [
    "scissor_analysis_stats.csv",
    "stance_data_with_scissor.csv",
    "data_refresh_status.json",
]

pack(
    app_file="scissor_explorer_app.py",
    extra_files_to_embed=[".streamlit/config.toml"],
    extra_files_to_link=DATA_FILES,
    prepend_github_path=GITHUB_REPO,
    requirements=[
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "numpy>=1.24.0",
    ],
    title="Scissor Kick Explorer",
    output_dir="docs",
    output_file="index.html",
    use_raw_api=False,
    js_bundle_version="0.85.1",
    stylesheet_version="0.85.1",
    run_preview_server=False,
    print_preview_message=True,
)

index_path = Path("docs/index.html")
html = index_path.read_text(encoding="utf-8")

data_links = "\n".join(
    f'  <app-file name="{name}" url="https://raw.githubusercontent.com/{GITHUB_REPO}/refs/heads/main/{name}"></app-file>'
    for name in DATA_FILES
)
if "raw.githubusercontent.com" not in html:
    html = html.replace("</streamlit-app>", f"{data_links}\n    </streamlit-app>", 1)

# Visible loading state while Pyodide boots (first visit can take 30-60s).
loading_block = """
    <div id="stlite-loading" style="font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 1.25rem 1.5rem; border: 1px solid #d0d7e2; border-radius: 12px; background: #f8fafc; color: #1d2f46;">
      <strong>Loading Scissor Kick Explorer…</strong>
      <p style="margin: 0.6rem 0 0;">This can take up to a minute on first visit while Python packages load in your browser.</p>
    </div>
"""
if "stlite-loading" not in html:
    html = html.replace("<body>", f"<body>{loading_block}", 1)
    index_path.write_text(html, encoding="utf-8")

print("GitHub Pages URL: https://angelozorn.github.io/baseball_scissor_kick_project/")

"""Build static Stlite bundle in docs/ and GitHub Actions workflow for GitHub Pages."""

from stlitepack import pack

DATA_FILES = [
    "scissor_analysis_stats.csv",
    "stance_data_with_scissor.csv",
    "data_refresh_status.json",
]

pack(
    app_file="scissor_explorer_app.py",
    extra_files_to_embed=DATA_FILES,
    requirements=[
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "numpy>=1.24.0",
    ],
    title="Scissor Kick Explorer",
    output_dir="docs",
    output_file="index.html",
    prepend_github_path="angelozorn/baseball_scissor_kick_project",
    use_raw_api=True,
    js_bundle_version="0.80.5",
    stylesheet_version="0.80.5",
    run_preview_server=False,
    print_preview_message=True,
)

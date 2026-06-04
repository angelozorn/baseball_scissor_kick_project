"""Build a GitHub Pages-ready Stlite bundle in docs/index.html."""

from __future__ import annotations

import json
from pathlib import Path

from stlitepack.pack import _material_icons_style

BASE_PATH = "baseball_scissor_kick_project"
GITHUB_REPO = f"angelozorn/{BASE_PATH}"
STLITE_VERSION = "0.85.1"

DATA_FILES = [
    "scissor_analysis_stats.csv",
    "stance_data_with_scissor.csv",
    "data_refresh_status.json",
]

ROOT = Path(__file__).resolve().parent


def escape_js_template_literal(content: str) -> str:
    """Escape Python source for embedding in a JS template literal."""
    return (
        content.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )


def js_files_object() -> str:
    entries: list[str] = []

    embedded = {
        "scissor_explorer_app.py": ROOT / "scissor_explorer_app.py",
        ".streamlit/config.toml": ROOT / ".streamlit/config.toml",
    }
    for name, path in embedded.items():
        code = path.read_text(encoding="utf-8")
        escaped = escape_js_template_literal(code)
        entries.append(f'{json.dumps(name)}: `\n{escaped}\n`')

    for name in DATA_FILES:
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/refs/heads/main/{name}"
        entries.append(f'{json.dumps(name)}: {{ url: {json.dumps(url)} }}')

    return "{\n          " + ",\n          ".join(entries) + "\n        }"


def build_index_html() -> str:
    requirements = json.dumps(
        ["pandas>=2.0.0", "matplotlib>=3.7.0", "numpy>=1.24.0"]
    )
    streamlit_config = json.dumps(
        {
            "server.baseUrlPath": BASE_PATH,
            "browser.gatherUsageStats": False,
        }
    )
    files_js = js_files_object()
    icons_style = _material_icons_style()

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Scissor Kick Explorer</title>
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE_VERSION}/build/stlite.css"
    />
    {icons_style}
    <style>
      html, body {{
        margin: 0;
        padding: 0;
        min-height: 100%;
        background: #f3f6fb;
      }}
      #stlite-loading {{
        font-family: system-ui, -apple-system, sans-serif;
        max-width: 640px;
        margin: 2rem auto;
        padding: 1.25rem 1.5rem;
        border: 1px solid #d0d7e2;
        border-radius: 12px;
        background: #f8fafc;
        color: #1d2f46;
      }}
      #stlite-error {{
        display: none;
        font-family: system-ui, -apple-system, sans-serif;
        max-width: 720px;
        margin: 2rem auto;
        padding: 1.25rem 1.5rem;
        border: 1px solid #f5c2c7;
        border-radius: 12px;
        background: #fff5f5;
        color: #7a1f2b;
      }}
      #root {{
        min-height: 100vh;
      }}
    </style>
  </head>
  <body>
    <div id="stlite-loading">
      <strong>Loading Scissor Kick Explorer…</strong>
      <p style="margin: 0.6rem 0 0;">
        First visit can take up to a minute while Python packages load in your browser.
      </p>
    </div>
    <div id="stlite-error"></div>
    <div id="root"></div>
    <script type="module">
      import {{ mount }} from "https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE_VERSION}/build/stlite.js";

      const loadingEl = document.getElementById("stlite-loading");
      const errorEl = document.getElementById("stlite-error");

      function showError(message) {{
        if (loadingEl) loadingEl.style.display = "none";
        if (errorEl) {{
          errorEl.style.display = "block";
          errorEl.textContent = message;
        }}
      }}

      Promise.resolve(
        mount(
          {{
            streamlitConfig: {streamlit_config},
            requirements: {requirements},
            entrypoint: "scissor_explorer_app.py",
            files: {files_js},
          }},
          document.getElementById("root")
        )
      )
        .then(() => {{
          if (loadingEl) loadingEl.style.display = "none";
        }})
        .catch((err) => {{
          console.error(err);
          showError(
            "The app failed to start in your browser. Try a hard refresh or another browser (Chrome/Edge/Safari). " +
              (err && err.message ? err.message : String(err))
          );
        }});
    </script>
  </body>
</html>
"""


def main() -> None:
    outdir = ROOT / "docs"
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / "index.html"
    outfile.write_text(build_index_html(), encoding="utf-8")
    print(f"Packed app written to {outfile}")
    print(f"GitHub Pages URL: https://angelozorn.github.io/{BASE_PATH}/")


if __name__ == "__main__":
    main()

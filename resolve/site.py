"""Root page for branch-based GitHub Pages deployment.

Pages serves the repository root, while the map lives in public/. Instead of a redirect (weaker
for search engines and slower for visitors), the root index.html is a copy of public/index.html
with <base href="public/"> so that every relative URL resolves inside public/. Regenerate it with
`python -m resolve site`; tests/test_frontend.py checks that it is in sync.
"""
from .paths import PUBLIC, REPO

MARKER = '<meta charset="utf-8">'


def root_index_html():
    html = (PUBLIC / "index.html").read_text(encoding="utf-8")
    if MARKER not in html:
        raise ValueError("public/index.html must contain <meta charset=\"utf-8\">")
    note = "<!-- Generated from public/index.html by `python -m resolve site`; do not edit. -->"
    return html.replace(MARKER, f'{MARKER}\n\t<base href="public/">\n\t{note}', 1)


def write_root_index():
    (REPO / "index.html").write_text(root_index_html(), encoding="utf-8", newline="\n")
    return "wrote index.html (root) from public/index.html"

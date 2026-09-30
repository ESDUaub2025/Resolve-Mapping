"""Frontend invariants: generic (catalog-driven), no HTML injection, pinned dependencies, bilingual UI."""
import json
import re

from resolve.paths import PUBLIC, PUBLIC_DATA

JS = sorted((PUBLIC / "js").glob("*.js"))


def test_no_dataset_or_layer_names_in_code():
    catalog = json.loads((PUBLIC_DATA / "catalog.json").read_text(encoding="utf-8"))
    names = {layer["id"] for layer in catalog["layers"]} | set(catalog["datasets"])
    pattern = re.compile(r"['\"`](" + "|".join(map(re.escape, sorted(names))) + r")['\"`]")
    offending = {p.name: pattern.findall(p.read_text(encoding="utf-8")) for p in JS}
    assert not any(offending.values()), f"dataset-specific literals in frontend: {offending}"


def test_no_html_injection_sinks():
    for p in JS:
        text = p.read_text(encoding="utf-8")
        assert "innerHTML" not in text and "insertAdjacentHTML" not in text and "document.write" not in text, p.name


def test_cdn_assets_pinned_with_sri():
    html = (PUBLIC / "index.html").read_text(encoding="utf-8")
    # Only resources the browser loads and executes/applies: scripts and stylesheets.
    tags = re.findall(r"<script[^>]+src=\"https://[^\"]+\"[^>]*>", html)
    tags += [t for t in re.findall(r"<link[^>]+href=\"https://[^\"]+\"[^>]*>", html) if 'rel="stylesheet"' in t]
    assert tags, "expected CDN script and stylesheet tags"
    for tag in tags:
        assert 'integrity="sha384-' in tag and 'crossorigin="anonymous"' in tag, tag


def test_ui_strings_exist_in_both_languages():
    text = (PUBLIC / "js" / "i18n.js").read_text(encoding="utf-8")
    en = text[text.index("en: {"):text.index("ar: {")]
    ar = text[text.index("ar: {"):]
    keys = lambda block: set(re.findall(r"^\t\t(\w+):", block, re.M))
    assert keys(en) == keys(ar), f"missing translations: {keys(en) ^ keys(ar)}"


def test_static_site_has_no_legacy_or_data_outside_release():
    allowed = {"index.html", "og-image.png", "css", "js", "data"}
    for p in PUBLIC.iterdir():
        assert p.name in allowed, f"unexpected item in public/: {p.name}"


def test_root_page_is_the_map_and_in_sync():
    from resolve.paths import REPO
    from resolve.site import root_index_html
    assert (REPO / "index.html").read_text(encoding="utf-8") == root_index_html(), "run: python -m resolve site"


def test_seo_metadata_present():
    html = (PUBLIC / "index.html").read_text(encoding="utf-8")
    for needle in ('<link rel="canonical"', 'name="description"', 'property="og:image"', 'application/ld+json',
                   '"@type": "Dataset"', 'data-i18n="aboutText"'):
        assert needle in html, needle

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
    for tag in re.findall(r"<(?:script|link)[^>]+(?:src|href)=\"https://[^\"]+\"[^>]*>", html):
        if "fonts" in tag:
            continue
        assert 'integrity="sha384-' in tag and 'crossorigin="anonymous"' in tag, tag


def test_ui_strings_exist_in_both_languages():
    text = (PUBLIC / "js" / "i18n.js").read_text(encoding="utf-8")
    en = text[text.index("en: {"):text.index("ar: {")]
    ar = text[text.index("ar: {"):]
    keys = lambda block: set(re.findall(r"^\t\t(\w+):", block, re.M))
    assert keys(en) == keys(ar), f"missing translations: {keys(en) ^ keys(ar)}"


def test_static_site_has_no_legacy_or_data_outside_release():
    allowed_dirs = {"css", "js", "data"}
    for p in PUBLIC.iterdir():
        assert p.is_file() and p.name == "index.html" or p.name in allowed_dirs, f"unexpected item in public/: {p.name}"

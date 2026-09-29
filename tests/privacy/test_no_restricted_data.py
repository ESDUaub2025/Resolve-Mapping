"""Privacy invariant: no restricted farmer-survey data may be tracked in this public repository.

Everything tracked here is served by GitHub Pages. Respondent consent covers research use only,
so raw survey files, respondent-level records, direct identifiers and ML outputs derived from
them must live in the private data store, never in this repository.

Build-breaking by design. If a later stage legitimately publishes new survey-derived products
(disclosure-controlled aggregates under public/), extend the allow-list here deliberately.
"""
import json
import re
import subprocess
from fnmatch import fnmatch
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# Paths removed in Stage 0; none may come back.
FORBIDDEN_PATHS = [
    "data/*.xlsx",
    "data/*.xls",
    "data/MZSurvey*",
    "data/survey_by_theme/*",
    "data/layers/*",
    "data/ml_prepared_data.csv",
    "data/canonical_audit/*",
    "data/conversion_audit/*",
    "data/coordinate_addition_audit.json",
    "data/models/*",
    "data/geojson/canonical/*",
    "data/geojson/Model_Predictions.geojson",
    "data/geojson/AI_Grid_Predictions.geojson",
    "data/geojson/Farmers_Boundary.geojson",
    "data/geojson/Water*.geojson",
    "data/geojson/Energy*.geojson",
    "data/geojson/Food*.geojson",
    "data/geojson/General_Info*.geojson",
    "data/geojson/Regenerative_Agriculture*.geojson",
]

# Spreadsheet/tabular formats that only ever held raw survey data here.
FORBIDDEN_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".sav", ".dta", ".parquet", ".joblib"}

DATA_EXTENSIONS = {".csv", ".tsv", ".json", ".geojson", ".txt"}

# Column headers of direct identifiers in the survey instruments (EN and AR).
IDENTIFIER_MARKERS = [
    "Respondent Name",
    "Name of respondent",
    "اسم المُستجيب",
    "اسم المستجيب",
    "رقم الهاتف",
    "phone number",
]

# Property keys that mark survey-derived features (village of a respondent or village aggregate).
SURVEY_PROPERTY_KEYS = {"القرية", "القرية:", "4. Village", "4.القرية:", "Village", "Village_Name", "respondent_id"}

# Lebanese mobile numbers; lookarounds exclude digits inside decimals, IDs and hex hashes.
PHONE_RE = re.compile(r"(?<![\w.])(?:\+?961[\s-]?|0)?(?:3|7[01689]|81)[\s-]?\d{3}[\s-]?\d{3}(?![\w.])")


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True
    ).stdout.decode("utf-8")
    return [p for p in out.split("\0") if p]


def data_files():
    return [p for p in tracked_files() if Path(p).suffix.lower() in DATA_EXTENSIONS and not p.startswith(".projectgraph/")]


def test_no_forbidden_paths_tracked():
    offending = [p for p in tracked_files() if any(fnmatch(p, pat) for pat in FORBIDDEN_PATHS)]
    assert offending == [], f"restricted survey/ML paths are tracked: {offending}"


def test_no_raw_tabular_formats_tracked():
    offending = [p for p in tracked_files() if Path(p).suffix.lower() in FORBIDDEN_EXTENSIONS]
    assert offending == [], f"raw tabular/model files are tracked: {offending}"


@pytest.mark.parametrize("path", data_files())
def test_no_identifier_columns(path):
    text = (REPO / path).read_text(encoding="utf-8", errors="ignore")
    found = [m for m in IDENTIFIER_MARKERS if m.lower() in text.lower()]
    assert found == [], f"{path} contains identifier columns {found}"


@pytest.mark.parametrize("path", data_files())
def test_no_phone_numbers(path):
    text = (REPO / path).read_text(encoding="utf-8", errors="ignore")
    matches = PHONE_RE.findall(text)
    assert matches == [], f"{path} contains {len(matches)} phone-number-like values"


@pytest.mark.parametrize("path", [p for p in data_files() if p.endswith(".geojson")])
def test_no_survey_derived_features(path):
    fc = json.loads((REPO / path).read_text(encoding="utf-8"))
    keys = set()
    for feature in fc.get("features", []):
        props = feature.get("properties") or {}
        keys.update(props)
        for nested in (props.get("values") or {}).values():
            if isinstance(nested, dict):
                keys.update(nested)
    overlap = keys & SURVEY_PROPERTY_KEYS
    assert not overlap, f"{path} carries survey-derived properties {sorted(overlap)}"

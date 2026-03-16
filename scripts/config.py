"""
Shared Python Configuration — mirrors app/config/manifest.js
=============================================================
This is the Python-side mirror of the JavaScript manifest.
The JS manifest is the canonical source of truth.
Run `python scripts/validate_data.py` to verify they stay in sync.
"""
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Theme definitions ────────────────────────────────────────────
# Keys match manifest.js THEMES keys (lowercase)
# PascalCase names used for file generation
THEMES = {
    'water': {
        'name': 'Water',
        'csvSources': {
            'ar': 'data/layers/Arabic/Water_1.0.csv',
            'en': 'data/layers/English/Water_1.0.en.csv',
        },
        'canonicalFiles': [
            'data/geojson/canonical/Water.canonical.geojson',
            'data/geojson/canonical/Water_new.canonical.geojson',
        ],
        'color': '#1abc9c',
    },
    'energy': {
        'name': 'Energy',
        'csvSources': {
            'ar': 'data/layers/Arabic/Energy_1.0.csv',
            'en': 'data/layers/English/Energy_1.0.en.csv',
        },
        'canonicalFiles': [
            'data/geojson/canonical/Energy.canonical.geojson',
            'data/geojson/canonical/Energy_new.canonical.geojson',
        ],
        'color': '#f39c12',
    },
    'food': {
        'name': 'Food',
        'csvSources': {
            'ar': 'data/layers/Arabic/Food_1.0.csv',
            'en': 'data/layers/English/Food_1.0.en.csv',
        },
        'canonicalFiles': [
            'data/geojson/canonical/Food.canonical.geojson',
            'data/geojson/canonical/Food_new.canonical.geojson',
        ],
        'color': '#9b59b6',
    },
    'general': {
        'name': 'General_Info',
        'csvSources': {
            'ar': 'data/layers/Arabic/Generalinfo_1.0.csv',
            'en': 'data/layers/English/Generalinfo_1.0.en.csv',
        },
        'canonicalFiles': [
            'data/geojson/canonical/General_Info.canonical.geojson',
            'data/geojson/canonical/General_Info_new.canonical.geojson',
        ],
        'color': '#2980b9',
    },
    'regen': {
        'name': 'Regenerative_Agriculture',
        'csvSources': {
            'ar': 'data/layers/Arabic/Regenerative_1.0.csv',
            'en': 'data/layers/English/Regenerative_1.0.en.csv',
        },
        'canonicalFiles': [
            'data/geojson/canonical/Regenerative_Agriculture.canonical.geojson',
            'data/geojson/canonical/Regenerative_Agriculture_new.canonical.geojson',
        ],
        'color': '#27ae60',
    },
}

# ── Static layers ────────────────────────────────────────────────
STATIC_LAYERS = {
    'fire': {
        'file': 'data/geojson/fire.geojson',
        'color': '#e74c3c',
    },
    'preservations': {
        'file': 'data/geojson/Preservations.geojson',
        'color': '#2ecc71',
    },
    'farmers': {
        'file': 'data/geojson/Model_Predictions.geojson',
        'color': '#16a085',
    },
}

# ── AI prediction layers ────────────────────────────────────────
AI_LAYERS = {
    'regen': {
        'predictionProp': 'Pred_Regen_Adoption',
        'type': 'binary',
    },
    'water': {
        'predictionProp': 'Pred_Water_Risk',
        'type': 'binary',
    },
    'econ': {
        'predictionProp': 'Pred_Production_Level',
        'type': 'ternary',
    },
    'climate': {
        'predictionProp': 'Pred_Climate_Vuln',
        'type': 'ternary',
    },
}

AI_SOURCE_FILE = 'data/geojson/Model_Predictions.geojson'
BOUNDARY_FILE = 'data/geojson/Farmers_Boundary.geojson'

# ── Coordinate bounds (Lebanon study area: Chouf + Beqaa) ────────
LAT_MIN, LAT_MAX = 33.40, 34.10
LON_MIN, LON_MAX = 35.20, 36.10  # extended for Beqaa Valley data

# ── Columns to exclude from GeoJSON properties ──────────────────
EXCLUDE_COLUMNS = ['X', 'Y', 'OBJECTID', 'FID']

# ── Helper ───────────────────────────────────────────────────────
def resolve(rel_path: str) -> Path:
    """Resolve a project-relative path to absolute."""
    return PROJECT_ROOT / rel_path

"""Temporary script to inspect actual data values for feature engineering fix."""
import json
from collections import Counter
from pathlib import Path

data_dir = Path("data/geojson/canonical")
themes = ['Water', 'Energy', 'Food', 'General_Info', 'Regenerative_Agriculture']
all_vals = {}

for theme in themes:
    for suffix in ['', '_new']:
        fp = data_dir / f"{theme}{suffix}.canonical.geojson"
        if not fp.exists():
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            gj = json.load(f)
        for feat in gj['features']:
            en = feat['properties'].get('values', {}).get('en', {})
            for k, v in en.items():
                key = f'{theme.lower()}__{k}'
                if key not in all_vals:
                    all_vals[key] = []
                all_vals[key].append(v)

# Show all keys with their value distributions
for key in sorted(all_vals.keys()):
    vals = [v for v in all_vals[key] if v and str(v).strip()]
    if vals:
        counts = Counter(vals)
        if len(counts) <= 20:  # Only show categorical-ish columns
            print(f'\n{key} ({len(vals)} non-empty, {len(counts)} unique):')
            for v, c in counts.most_common(20):
                print(f'  "{v}" ({c})')

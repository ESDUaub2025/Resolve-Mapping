#!/usr/bin/env python3
"""
RESOLVE Map — Data & Config Validation Suite
=============================================
Validates data integrity, config synchronization, and bilingual parity.
Run from project root:  python scripts/validate_data.py

Exit codes:
  0 = all checks passed
  1 = one or more checks failed
"""
import json
import re
import sys
from pathlib import Path

# Import shared config
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    THEMES, STATIC_LAYERS, AI_LAYERS, AI_SOURCE_FILE, BOUNDARY_FILE,
    LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, PROJECT_ROOT, resolve,
)

PASS = 0
FAIL = 0


def check(label: str, ok: bool, detail: str = ''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'  ✓ {label}')
    else:
        FAIL += 1
        msg = f'  ✗ {label}'
        if detail:
            msg += f'  →  {detail}'
        print(msg)
    return ok


def section(title: str):
    print(f'\n{"="*60}\n  {title}\n{"="*60}')


# ─────────────────────────────────────────────────────────────────
# 1. Canonical GeoJSON file integrity
# ─────────────────────────────────────────────────────────────────
def validate_canonical_files():
    section('1. Canonical GeoJSON Files')
    for key, cfg in THEMES.items():
        for rel in cfg['canonicalFiles']:
            path = resolve(rel)
            exists = path.exists()
            check(f'{rel} exists', exists)
            if not exists:
                continue

            with open(path, encoding='utf-8') as f:
                data = json.load(f)

            is_fc = data.get('type') == 'FeatureCollection'
            check(f'  type=FeatureCollection', is_fc)

            features = data.get('features', [])
            check(f'  features > 0', len(features) > 0, f'got {len(features)}')

            # Check structure of first feature
            feat = features[0]
            props = feat.get('properties', {})
            check(f'  has featureId', 'featureId' in props)
            check(f'  has theme', 'theme' in props)
            vals = props.get('values', {})
            check(f'  has values.ar', 'ar' in vals)
            check(f'  has values.en', 'en' in vals)

            # Bilingual parity: en and ar should have same number of keys
            if 'ar' in vals and 'en' in vals:
                ar_keys = set(vals['ar'].keys())
                en_keys = set(vals['en'].keys())
                parity = len(ar_keys) == len(en_keys)
                check(f'  bilingual key count parity', parity,
                      f'ar={len(ar_keys)} en={len(en_keys)}')

            # Coordinate bounds check
            bad_coords = 0
            for ft in features:
                coords = ft.get('geometry', {}).get('coordinates', [])
                if len(coords) >= 2:
                    lon, lat = coords[0], coords[1]
                    if not (LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX):
                        bad_coords += 1
            check(f'  all coords in Lebanon bounds', bad_coords == 0,
                  f'{bad_coords} features outside [{LON_MIN}-{LON_MAX}]E [{LAT_MIN}-{LAT_MAX}]N')


# ─────────────────────────────────────────────────────────────────
# 2. Static layer files
# ─────────────────────────────────────────────────────────────────
def validate_static_files():
    section('2. Static Layer Files')
    for name, cfg in STATIC_LAYERS.items():
        path = resolve(cfg['file'])
        exists = path.exists()
        check(f'{cfg["file"]} exists', exists)
        if not exists:
            continue

        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        features = data.get('features', [])
        check(f'  {name}: {len(features)} features > 0', len(features) > 0)


# ─────────────────────────────────────────────────────────────────
# 3. AI / ML output files
# ─────────────────────────────────────────────────────────────────
def validate_ai_files():
    section('3. AI / ML Output Files')

    # Model predictions
    pred_path = resolve(AI_SOURCE_FILE)
    exists = pred_path.exists()
    check(f'{AI_SOURCE_FILE} exists', exists)
    if exists:
        with open(pred_path, encoding='utf-8') as f:
            data = json.load(f)
        features = data.get('features', [])
        check(f'  features > 0', len(features) > 0, f'got {len(features)}')

        # Check prediction properties present
        if features:
            sample = features[0].get('properties', {})
            for ai_key, ai_cfg in AI_LAYERS.items():
                prop = ai_cfg['predictionProp']
                check(f'  has {prop}', prop in sample)

    # Boundary
    bound_path = resolve(BOUNDARY_FILE)
    check(f'{BOUNDARY_FILE} exists', bound_path.exists())

    # Grid predictions
    grid_path = resolve('data/geojson/AI_Grid_Predictions.geojson')
    grid_exists = grid_path.exists()
    check(f'AI_Grid_Predictions.geojson exists', grid_exists)
    if grid_exists:
        with open(grid_path, encoding='utf-8') as f:
            grid = json.load(f)
        check(f'  grid features > 100', len(grid.get('features', [])) > 100,
              f'got {len(grid.get("features", []))}')

    # Trained models
    for target in ['regen_adoption', 'water_risk', 'economic_vuln', 'climate_vuln']:
        model_path = resolve(f'data/models/target_{target}_model.joblib')
        check(f'  model: target_{target}_model.joblib', model_path.exists())


# ─────────────────────────────────────────────────────────────────
# 4. CSV source files
# ─────────────────────────────────────────────────────────────────
def validate_csv_sources():
    section('4. CSV Source Files')
    for key, cfg in THEMES.items():
        for lang, rel in cfg['csvSources'].items():
            path = resolve(rel)
            check(f'{rel}', path.exists())


# ─────────────────────────────────────────────────────────────────
# 5. JS manifest ↔ Python config sync
# ─────────────────────────────────────────────────────────────────
def validate_config_sync():
    section('5. JS Manifest ↔ Python Config Sync')
    manifest_path = resolve('app/config/manifest.js')
    if not manifest_path.exists():
        check('manifest.js exists', False)
        return

    js_text = manifest_path.read_text(encoding='utf-8')

    # Check theme colors match
    for key, cfg in THEMES.items():
        py_color = cfg['color']
        # Look for pattern like: key: { ... color: '#hex' ... }
        # Simplified check: just verify the color hex appears in the JS file
        check(f'  {key} color {py_color} in manifest.js', py_color in js_text)

    # Check canonical file paths match
    for key, cfg in THEMES.items():
        for rel in cfg['canonicalFiles']:
            check(f'  {rel} in manifest.js', rel in js_text)

    # Check static layer files match
    for name, cfg in STATIC_LAYERS.items():
        check(f'  static {name} file in manifest.js', cfg['file'] in js_text)

    # Check AI prediction props match
    for ai_key, ai_cfg in AI_LAYERS.items():
        prop = ai_cfg['predictionProp']
        check(f'  AI prop {prop} in manifest.js', prop in js_text)


# ─────────────────────────────────────────────────────────────────
# 6. HTML ↔ Manifest layer ID sync
# ─────────────────────────────────────────────────────────────────
def validate_html_layers():
    section('6. HTML data-layer ↔ Manifest Sync')
    html_path = resolve('index.html')
    if not html_path.exists():
        check('index.html exists', False)
        return

    html = html_path.read_text(encoding='utf-8')
    layer_ids = set(re.findall(r'data-layer="([^"]+)"', html))
    check(f'  found {len(layer_ids)} data-layer attributes', len(layer_ids) > 0)

    manifest_path = resolve('app/config/manifest.js')
    if not manifest_path.exists():
        return

    js = manifest_path.read_text(encoding='utf-8')

    # Extract theme layerIds from manifest (look for the actual object keys)
    # Match pattern: water: { \n layerId: 'water-points' in THEMES block
    all_layer_ids = re.findall(r"layerId:\s*'([^']+)'", js)

    # Theme layer IDs (first 5 matching *-points pattern)
    theme_ids = [lid for lid in all_layer_ids if lid.endswith('-points') and not lid.startswith('ai-') and lid not in ('fire-points', 'farmers-points')]
    for lid in theme_ids:
        check(f'  theme data-layer="{lid}" in HTML', lid in layer_ids)

    # AI layer IDs
    ai_ids = [lid for lid in all_layer_ids if lid.startswith('ai-')]
    for lid in ai_ids:
        in_html = lid in layer_ids or lid in html  # may be commented out
        check(f'  AI data-layer="{lid}" in HTML', in_html)

    # Note: fire-points, fire-heatmap, farmers-points are programmatically toggled


# ─────────────────────────────────────────────────────────────────
# 7. Feature ID stability
# ─────────────────────────────────────────────────────────────────
def validate_feature_ids():
    section('7. Feature ID Stability')
    seen_ids = set()
    duplicates = []
    for key, cfg in THEMES.items():
        for rel in cfg['canonicalFiles']:
            path = resolve(rel)
            if not path.exists():
                continue
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            for feat in data.get('features', []):
                fid = feat.get('properties', {}).get('featureId', '')
                if fid in seen_ids:
                    duplicates.append(fid)
                seen_ids.add(fid)
    check(f'  {len(seen_ids)} unique feature IDs', len(seen_ids) > 0)
    check(f'  no duplicate IDs across themes', len(duplicates) == 0,
          f'{len(duplicates)} dupes: {duplicates[:5]}')


# ─────────────────────────────────────────────────────────────────
# 8. Bilingual content quality
# ─────────────────────────────────────────────────────────────────
def validate_bilingual_quality():
    section('8. Bilingual Content Quality')
    for key, cfg in THEMES.items():
        for rel in cfg['canonicalFiles']:
            path = resolve(rel)
            if not path.exists():
                continue

            with open(path, encoding='utf-8') as f:
                data = json.load(f)

            features = data.get('features', [])
            if not features:
                continue

            identical_count = 0
            total = 0
            for feat in features:
                vals = feat.get('properties', {}).get('values', {})
                ar_vals = vals.get('ar', {})
                en_vals = vals.get('en', {})
                # Count features where EN values are identical to AR values
                # (indicating missing translation)
                if ar_vals and en_vals:
                    total += 1
                    # Compare a non-trivial subset of values
                    ar_str = json.dumps(ar_vals, ensure_ascii=False, sort_keys=True)
                    en_str = json.dumps(en_vals, ensure_ascii=False, sort_keys=True)
                    if ar_str == en_str:
                        identical_count += 1

            if total > 0:
                pct = (identical_count / total) * 100
                ok = pct < 50  # Allow some (coordinates/numbers may match)
                basename = Path(rel).name
                check(f'  {basename}: {pct:.0f}% identical EN/AR',
                      ok, f'{identical_count}/{total} features have identical values')


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    print(f'\nRESOLVE Map Validation Suite')
    print(f'Project root: {PROJECT_ROOT}\n')

    validate_canonical_files()
    validate_static_files()
    validate_ai_files()
    validate_csv_sources()
    validate_config_sync()
    validate_html_layers()
    validate_feature_ids()
    validate_bilingual_quality()

    section('RESULTS')
    total = PASS + FAIL
    print(f'  {PASS}/{total} checks passed, {FAIL} failed')
    if FAIL == 0:
        print('  All validations passed! ✓')
    else:
        print(f'  ⚠ {FAIL} issue(s) found — review above')

    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

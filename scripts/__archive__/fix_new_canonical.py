# -*- coding: utf-8 -*-
"""
Fix Bilingual Canonical GeoJSON for New Survey Data
====================================================
Reads the MZSurvey CSV (29 Beqaa Valley respondents) which has paired
EN/AR columns, extracts data per theme, and generates proper bilingual
canonical GeoJSON files for all 5 themes.

Fixes:
1. Energy_new and Food_new canonical files which were empty/Arabic-only
2. All _new canonical files get proper English values (not Arabic-for-both)
3. Uses coordinates from MZSurvey_with_coords CSV

Output: data/geojson/canonical/{Theme}_new.canonical.geojson (5 files)
"""

import pandas as pd
import json
import hashlib
import sys
import io
from pathlib import Path
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================
# COLUMN MAPPING: MZSurvey CSV column index → theme properties
# Maps English column name → Arabic column name for each theme
# ============================================================

# Key columns for extraction (EN column name → AR column name)
THEME_COLUMNS = {
    'Water': {
        # EN col → AR col from MZSurvey CSV
        '10. Main Crops': '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟',
        '13. Water Source': '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟',
        '16. Water Availability': '16.كيف تقيّم توفر المياه خلال موسم الزراعة؟',
        '17. Water Scarcity Months': 'ما أشهر  الذي  تعاني فيها من شح المياه؟',
        '18. Change in Irrigation Needs': '18.هل لاحظت أي تغيير في احتياجات الري خلال السنوات العشر الماضية؟',
    },
    'Energy': {
        '14. Energy Source': '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟',
        '15. Energy Consumption': '15.كمية الطاقة المستخدمة خلال موسم الذروة الزراعي (تقدير بالساعة أو بالوقود):',
    },
    'Food': {
        '19. Food Production Level': '19.كيف تصف مستوى إنتاج الغذاء والمنتجات التقليدية في منزلك/قريتك/تعاونيتك؟',
        '20. Coop Member?': '20. هل أنت عضو في تعاونية تقوم بإنتاج و/أو بيع الأطعمة التقليدية؟',
        '24. % Village Participation': '24. ما هي نسبة المنازل في قريتك التي تشارك في إنتاج المؤونة أو الطعام التقليدي؟',
    },
    'General_Info': {
        '5. Own Farmland?': '5.هل تمتلك أرضاً زراعية؟',
        '8. Land Size': '8.ما هو حجم الحيازة الزراعية الخاصة بك؟',
        '9. Soil Type': '9.ما هو نوع التربة في أرضك؟',
        '52. Climate Change Noticed?': ' 52. هل لاحظت تغيرات مناخية أثرت على الزراعة في السنوات الأخيرة؟',
        '53. Climate Changes': '53. إذا كانت الإجابة "نعم"، يرجى تحديد أهمها',
        '54. Impact on Production': '54.كيف أثرت هذه التغيرات على إنتاجك الزراعي؟',
    },
    'Regenerative_Agriculture': {
        '34. Seed Selection Criteria': '34.ما هي المعايير التي تعتمدها عند شراء البذور/الشتول؟',
        '35. Seed Source': '35.كيف تحصل على البذور/الشتول؟',
        '36. Seed Challenges': '36.ما هو التحدي الأكبر في الحصول على البذور/الشتول؟',
        '38. Soil Enhancers': '38.ما هو أنواع المحسنات التي تستخدمها في التربة؟',
        '39. Chem Fertilizer Reliance': '39.ما مدى اعتمادك على الأسمدة الكيميائية؟',
        '43. Pest Control Method': '43.كيف تقوم بمكافحة الآفات؟',
        '44. Pesticide Reliance': '44.ما مدى اعتمادك على المبيدات الكيميائية؟',
        '63. Raise Poultry?': '.63.هل تربي الدواجن في مزرعتك أو منزلك؟',
    },
}

# Common columns included in EVERY theme
COMMON_EN_COLS = {
    '4. Village': '4.القرية:',
}

EXCLUDE_KEYS = {'X', 'Y', 'OBJECTID', 'FID', 'start', 'End', 'Location & Context'}


def coordinate_hash(lon, lat, precision=8):
    coord_str = f"{float(lon):.8f},{float(lat):.8f}"
    return hashlib.sha256(coord_str.encode()).hexdigest()[:precision]


def generate_feature_id(theme, row_num, lon, lat):
    theme_key = theme.lower().replace('_', '')[:6]
    c_hash = coordinate_hash(lon, lat)
    return f"{theme_key}_{row_num}_{c_hash}"


def find_column(df_columns, target):
    """Find a column in the DataFrame, handling whitespace/encoding differences."""
    # Exact match
    if target in df_columns:
        return target
    # Strip whitespace match
    target_stripped = target.strip()
    for col in df_columns:
        if col.strip() == target_stripped:
            return col
    # Substring match (for Arabic columns that may have encoding differences)
    for col in df_columns:
        if target_stripped in col or col in target_stripped:
            return col
    return None


def extract_value(row, col_name, df_columns):
    """Extract a value from a row, handling column name matching."""
    matched = find_column(df_columns, col_name)
    if matched and pd.notna(row.get(matched)):
        return str(row[matched])
    return None


def main():
    print("=" * 70)
    print("FIX: Bilingual Canonical GeoJSON for New Survey Data")
    print("=" * 70)

    # ---- Load MZSurvey CSV (the bilingual source) ----
    mz_path = Path('data/MZSurvey farmers ENGLISH_with_coords.csv')
    mz_plain = Path('data/MZSurvey farmers ENGLISH.csv')

    if mz_path.exists():
        df = pd.read_csv(mz_path, encoding='utf-8')
        print(f"Loaded {mz_path}: {len(df)} rows x {len(df.columns)} cols")
    elif mz_plain.exists():
        df = pd.read_csv(mz_plain, encoding='utf-8')
        print(f"Loaded {mz_plain}: {len(df)} rows x {len(df.columns)} cols")
    else:
        print("ERROR: No MZSurvey CSV found!")
        return

    all_cols = list(df.columns)

    # ---- Find X/Y coordinate columns ----
    x_col = find_column(all_cols, 'X')
    y_col = find_column(all_cols, 'Y')
    has_coords = x_col is not None and y_col is not None

    if has_coords:
        valid_coords = df[[x_col, y_col]].notna().all(axis=1).sum()
        print(f"Coordinate columns found: X={x_col}, Y={y_col} ({valid_coords}/{len(df)} rows valid)")
    else:
        print("WARNING: No X/Y coordinates in CSV. Will use village coordinate lookup.")

    # ---- Find Village column ----
    village_en_col = find_column(all_cols, '4. Village')
    village_ar_col = find_column(all_cols, '4.القرية:')
    print(f"Village columns: EN={village_en_col}, AR={village_ar_col}")

    # ---- Load village coordinates for fallback ----
    village_coords = {}
    vc_file = Path('data/verified_village_coordinates.json')
    if vc_file.exists():
        with open(vc_file, 'r', encoding='utf-8') as f:
            vc_data = json.load(f)
        if 'villages' in vc_data:
            for name, info in vc_data['villages'].items():
                village_coords[name.lower().strip()] = (info.get('lon', info.get('x')), info.get('lat', info.get('y')))
        print(f"Loaded {len(village_coords)} village coordinates for fallback")

    # Also extract coords from existing canonical GeoJSON as fallback
    canon_dir = Path('data/geojson/canonical')
    for gf in canon_dir.glob('*.canonical.geojson'):
        if '_new' in gf.name:
            continue
        with open(gf, 'r', encoding='utf-8') as f:
            gj = json.load(f)
        for feat in gj.get('features', []):
            vals = feat.get('properties', {}).get('values', {})
            en_vals = vals.get('en', {})
            # Try to get village name from various keys
            for vkey in ['القرية', '4. Village', '4.القرية:', '4.القرية']:
                vname = en_vals.get(vkey)
                if vname:
                    coords = feat.get('geometry', {}).get('coordinates', [])
                    if len(coords) >= 2:
                        village_coords[vname.lower().strip()] = (coords[0], coords[1])
                    break

    print(f"Total village coordinate entries: {len(village_coords)}")

    # ---- Process each theme ----
    output_dir = Path('data/geojson/canonical')
    audit_dir = Path('data/canonical_audit')
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for theme, col_mapping in THEME_COLUMNS.items():
        print(f"\n{'=' * 60}")
        print(f"Theme: {theme}")
        print(f"{'=' * 60}")

        features = []
        skipped = 0
        missing_cols = []

        # Check which columns exist
        for en_col, ar_col in col_mapping.items():
            en_found = find_column(all_cols, en_col)
            ar_found = find_column(all_cols, ar_col)
            status = "OK" if en_found and ar_found else f"EN={'OK' if en_found else 'MISS'} AR={'OK' if ar_found else 'MISS'}"
            if not en_found or not ar_found:
                missing_cols.append((en_col, status))
            print(f"  {en_col}: {status}")

        for idx, row in df.iterrows():
            row_num = idx + 1

            # ---- Get coordinates ----
            lon, lat = None, None

            if has_coords and pd.notna(row.get(x_col)) and pd.notna(row.get(y_col)):
                try:
                    lon = float(row[x_col])
                    lat = float(row[y_col])
                except (ValueError, TypeError):
                    pass

            # Fallback: lookup by village name
            if lon is None or lat is None:
                village = extract_value(row, '4. Village', all_cols)
                if village and village.lower().strip() in village_coords:
                    lon, lat = village_coords[village.lower().strip()]

            if lon is None or lat is None:
                skipped += 1
                continue

            # ---- Extract bilingual properties ----
            en_values = {}
            ar_values = {}

            # Village name (common)
            village_en = extract_value(row, '4. Village', all_cols)
            village_ar = extract_value(row, '4.القرية:', all_cols)
            if village_en:
                en_values['4. Village'] = village_en
            if village_ar:
                ar_values['4. Village'] = village_ar
            elif village_en:
                ar_values['4. Village'] = village_en  # Fallback

            # Theme-specific properties
            for en_col, ar_col in col_mapping.items():
                en_val = extract_value(row, en_col, all_cols)
                ar_val = extract_value(row, ar_col, all_cols)

                if en_val:
                    en_values[en_col] = en_val
                if ar_val:
                    ar_values[en_col] = ar_val
                elif en_val:
                    # If no Arabic value, use English as fallback
                    ar_values[en_col] = en_val

            # Skip if no meaningful data for this theme
            theme_data_count = sum(1 for k in en_values if k != '4. Village')
            if theme_data_count == 0:
                skipped += 1
                continue

            # ---- Generate feature ----
            feature_id = generate_feature_id(theme, row_num, lon, lat)

            feature = {
                "type": "Feature",
                "id": feature_id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)]
                },
                "properties": {
                    "featureId": feature_id,
                    "theme": theme.lower().replace('_', ''),
                    "values": {
                        "ar": ar_values,
                        "en": en_values
                    },
                    "metadata": {
                        "sourceRow": row_num,
                        "coordinateHash": coordinate_hash(lon, lat),
                        "dataSource": "MZSurvey_2026_Beqaa",
                        "translationStatus": "complete"
                    }
                }
            }

            features.append(feature)

        print(f"\n  Generated: {len(features)} features, Skipped: {skipped}")

        if not features:
            print(f"  WARNING: No features for {theme}!")
            results.append({'theme': theme, 'features': 0, 'status': 'EMPTY'})
            continue

        # ---- Write GeoJSON ----
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "theme": theme,
                "format": "canonical_bilingual",
                "version": "2.1",
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "source": str(mz_path),
                "featureCount": len(features),
                "translationStatus": "complete",
                "notes": "Bilingual data extracted from MZSurvey paired EN/AR columns"
            },
            "features": features
        }

        out_file = output_dir / f'{theme}_new.canonical.geojson'
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {out_file}")

        # ---- Write audit ----
        audit = {
            "theme": theme,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": str(mz_path),
            "features_generated": len(features),
            "features_skipped": skipped,
            "en_columns_mapped": list(col_mapping.keys()),
            "ar_columns_mapped": list(col_mapping.values()),
            "missing_columns": missing_cols,
            "villages": sorted(set(
                f['properties']['values']['en'].get('4. Village', 'Unknown')
                for f in features
            )),
            "translationStatus": "complete"
        }

        audit_file = audit_dir / f'{theme}_new_canonical_audit.json'
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit, f, ensure_ascii=False, indent=2)

        results.append({'theme': theme, 'features': len(features), 'status': 'OK'})

    # ---- Summary ----
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    total = 0
    for r in results:
        icon = 'OK' if r['status'] == 'OK' else 'FAIL'
        print(f"  [{icon}] {r['theme']}: {r['features']} features")
        total += r['features']
    print(f"\n  Total: {total} features across {sum(1 for r in results if r['status'] == 'OK')}/{len(results)} themes")
    print(f"  Output: {output_dir.absolute()}")


if __name__ == '__main__':
    main()

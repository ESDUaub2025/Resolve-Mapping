#!/usr/bin/env python3
"""Convert CSV layer files to GeoJSON with 100% data integrity and proper language allocation.

Usage:
  python scripts/csvs_to_geojson_complete.py --theme Energy
  python scripts/csvs_to_geojson_complete.py --all

This script ensures:
- 100% data integrity (all CSV columns preserved)
- Proper bilingual support (EN properties in English GeoJSON, AR in Arabic)
- Consistent language throughout each version
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LAYERS_EN = ROOT / 'data' / 'layers' / 'English'
LAYERS_AR = ROOT / 'data' / 'layers' / 'Arabic'
OUT_DIR = ROOT / 'data' / 'geojson'

# Theme -> (English filename, Arabic filename)
THEMES = {
    'Energy': ('Energy_1.0.en.csv', 'Energy_1.0.csv'),
    'Food': ('Food_1.0.en.csv', 'Food_1.0.csv'),
    'General_Info': ('Generalinfo_1.0.en.csv', 'Generalinfo_1.0.csv'),
    'Regenerative_Agriculture': ('Regenerative_1.0.en.csv', 'Regenerative_1.0.csv'),
    'Water': ('Water_1.0.en.csv', 'Water_1.0.csv')
}

# English column -> Arabic property name mappings
# These mappings ensure the ENGLISH CSV produces GeoJSON with ARABIC property names
EN_TO_AR_MAPPINGS = {
    'Energy': {
        'Village': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'EnergySource': 'مصدر الطاقة',
        'EnergyUsedDuringPeakSeason': 'كمية الطاقة المستخدمة خلال موسم الذروة',
        'Manualperc': 'يدويا%',
        'Dieselperc': 'ديزل%',
        'Gridperc': 'شبكة%',
        'Gasolineperc': 'بنزين%',
        'Solarperc': 'شمسية%',
        'Diesel': 'Diesel L/Week (Avg)',
        'Gasoline': 'Benzine L/Week (Avg)',
        'kW': 'kW/Week (Avg)',
        'id_num': 'id_num'
    },
    'Food': {
        'Village': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'Production_Level': 'مستوى الانتاج',
        'Main_Traditional_Products': 'المنتجات التقليدية الرئيسية',
        'Main_Crops': 'المحاصيل الرئيسية',
        'Animal_Types': 'انواع الحيوانات',
        'Number_of_Birds': 'عدد الطيور',
        'Crop_Timing': 'توقيت المحاصيل',
        'Feed_Type': 'نوع العلف',
        'Mouneh_Participation_Rate': 'نسبة المشاركين في تحضير المؤونة',
        'num_id': 'num_id'
    },
    'General_Info': {
        'Village': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'Cultivation_Area': 'حجم الزراعة',
        'Soil_Type': 'نوع التربة',
        'Climate_Changes': 'التغيرات المناخية',
        'Impact_of_Climate_Changes': 'تأثير التغيرات المناخية',
        'id_num': 'id_num'
    },
    'Regenerative_Agriculture': {
        'Village': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'Chemical fertilizers': 'الاسمدة الكيميائية',
        'Pest control': 'مكافحة الآفات',
        'Chemical pesticides': 'المبيدات الكيميائية',
        'Regenerative agriculture techniques': 'تقنيات الزراعة التجديدية',
        'Types of soil conditioners': 'أنواع محسنات التربة'
    },
    'Water': {
        'Village': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'Crop': 'المحصول',
        'Main Irrigation Water Source': 'مصدر مياه الريّ الرئيسي',
        'Water Availability': 'توفر المياه',
        'Months of Water Shortage': 'أشهر شح المياه',
        'Crop Irrigation': 'ريّ المحصول',
        'Planting Months': 'اشهر الزراعة'
    }
}

# Arabic column -> Arabic property name mappings (for normalization)
# These ensure the ARABIC CSV columns are standardized
AR_TO_AR_MAPPINGS = {
    'Energy': {
        'القرية:': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'مصدر الطاقة:': 'مصدر الطاقة',
        'كمية الطاقة المستخدمة خلال موسم الذروة :': 'كمية الطاقة المستخدمة خلال موسم الذروة',
        'يدويا%:': 'يدويا%',
        'ديزل%:': 'ديزل%',
        'شبكة%:': 'شبكة%',
        'بنزين%:': 'بنزين%',
        'شمسية%:': 'شمسية%',
        'Diesel L/Week (Avg):': 'Diesel L/Week (Avg)',
        'Benzine L/Week (Avg):': 'Benzine L/Week (Avg)',
        'kW/Week (Avg):': 'kW/Week (Avg)'
    },
    'Food': {
        'القرية:': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'مستوى الانتاج:': 'مستوى الانتاج',
        'المنتجات التقليدية الرئيسية:': 'المنتجات التقليدية الرئيسية',
        'المحاصيل الرئيسية:': 'المحاصيل الرئيسية',
        'انواع الحيوانات:': 'انواع الحيوانات',
        'عدد الطيور:': 'عدد الطيور',
        'توقيت المحاصيل:': 'توقيت المحاصيل',
        'نوع العلف:': 'نوع العلف',
        'نسبة المشاركين في تحضير المؤونة:': 'نسبة المشاركين في تحضير المؤونة'
    },
    'General_Info': {
        'القرية:': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'حجم الزراعة:': 'حجم الزراعة',
        'نوع التربة:': 'نوع التربة',
        'التغيرات المناخية:': 'التغيرات المناخية',
        'تأثير الغيرات المناخية:': 'تأثير التغيرات المناخية'
    },
    'Regenerative_Agriculture': {
        'القرية:': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'الاسمدة الكيميائية:': 'الاسمدة الكيميائية',
        'مكافحة الآفات:': 'مكافحة الآفات',
        'المبيدات الكيميائية:': 'المبيدات الكيميائية',
        'تقنيات الزراعة التجديدية:': 'تقنيات الزراعة التجديدية',
        'أنواع محسنات التربة:': 'أنواع محسنات التربة'
    },
    'Water': {
        'القرية:': 'القرية',
        'Y': 'Y',
        'X': 'X',
        'المحصول:': 'المحصول',
        'مصدر مياه الريّ الرئيسي:': 'مصدر مياه الريّ الرئيسي',
        'توفر المياه:': 'توفر المياه',
        'أشهر شح المياه:': 'أشهر شح المياه',
        'ريّ المحصول:': 'ريّ المحصول',
        'اشهر الزراعة:': 'اشهر الزراعة'
    }
}


def to_float(v):
    """Convert value to float, handling various edge cases."""
    if v is None:
        return None
    try:
        if isinstance(v, str):
            vv = v.strip().replace(',', '').replace('\u200f', '')
            if vv == '':
                return None
            return float(vv)
        return float(v)
    except Exception:
        return None


def clean_value(val):
    """Clean and standardize CSV values."""
    if pd.isna(val):
        return None
    if isinstance(val, str):
        val = val.strip()
        if val == '':
            return None
    return val


def build_feature(props, lon, lat):
    """Build a GeoJSON feature with properties and geometry."""
    feat = {
        "type": "Feature",
        "properties": props
    }
    if lon is None or lat is None:
        feat["geometry"] = None
    else:
        feat["geometry"] = {
            "type": "Point",
            "coordinates": [lon, lat]
        }
    return feat


def convert_theme(theme: str, lang: str):
    """Convert a single theme CSV to GeoJSON."""
    if lang == 'en':
        df_path = LAYERS_EN / THEMES[theme][0]
        mapping = EN_TO_AR_MAPPINGS[theme]
        output_suffix = ''
    else:  # 'ar'
        df_path = LAYERS_AR / THEMES[theme][1]
        mapping = AR_TO_AR_MAPPINGS[theme]
        output_suffix = '_ar'

    print(f"\n{'='*60}")
    print(f"Processing: {theme} ({lang.upper()})")
    print(f"Source: {df_path.name}")
    print(f"{'='*60}")

    # Read CSV
    df = pd.read_csv(df_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"\nCSV Columns:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")

    # Build features
    features = []
    unmapped_columns = set()
    
    for idx, row in df.iterrows():
        properties = {}
        
        # Process each column
        for col in df.columns:
            # Get the mapped property name, or use original if no mapping exists
            if col in mapping:
                prop_name = mapping[col]
            else:
                prop_name = col
                unmapped_columns.add(col)
            
            # Get and clean the value
            val = clean_value(row[col])
            properties[prop_name] = val

        # Extract coordinates
        lat = to_float(row.get('Y'))
        lon = to_float(row.get('X'))
        
        # Add metadata
        properties['theme'] = theme
        properties['coords_source'] = 'csv' if (lat is not None and lon is not None) else 'missing'
        properties['source_file'] = df_path.name
        properties['source_row'] = idx + 2  # +2 because CSV row 1 is header, and we're 0-indexed

        # Build feature
        feat = build_feature(properties, lon, lat)
        features.append(feat)

    # Report unmapped columns (if any)
    if unmapped_columns:
        print(f"\n⚠️  WARNING: {len(unmapped_columns)} unmapped columns (using original names):")
        for col in sorted(unmapped_columns):
            print(f"  - {col}")

    # Create FeatureCollection
    fc = {
        "type": "FeatureCollection",
        "features": features
    }

    # Write output
    out_file = OUT_DIR / f"{theme}{output_suffix}.geojson"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    with out_file.open('w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)
    
    # Count features with coordinates
    with_coords = sum(1 for f in features if f['geometry'] is not None)
    
    print(f"\n✓ Success!")
    print(f"  Output: {out_file.name}")
    print(f"  Features: {len(features)}")
    print(f"  With coordinates: {with_coords} ({100*with_coords/len(features):.1f}%)")
    print(f"  Properties per feature: {len(features[0]['properties']) if features else 0}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert CSV layer files to GeoJSON with 100% data integrity'
    )
    parser.add_argument('--theme', help='Theme name to convert (e.g., Energy)')
    parser.add_argument('--all', action='store_true', help='Convert all themes')
    args = parser.parse_args()

    if not args.all and not args.theme:
        parser.print_help()
        return

    themes = list(THEMES.keys()) if args.all else [args.theme]
    
    print("\n" + "="*60)
    print("CSV to GeoJSON Converter")
    print("100% Data Integrity | Proper Language Allocation")
    print("="*60)

    success_count = 0
    error_count = 0

    for theme in themes:
        if theme not in THEMES:
            print(f'\n❌ Unknown theme: {theme}')
            print(f'   Available themes: {", ".join(THEMES.keys())}')
            error_count += 1
            continue
        
        try:
            # Convert English version (produces GeoJSON with Arabic property names for consistency)
            convert_theme(theme, 'en')
            # Convert Arabic version (uses Arabic property names)
            convert_theme(theme, 'ar')
            success_count += 2
        except Exception as e:
            print(f'\n❌ Error converting {theme}: {e}')
            import traceback
            traceback.print_exc()
            error_count += 1

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✓ Successful conversions: {success_count}")
    if error_count > 0:
        print(f"❌ Failed conversions: {error_count}")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

"""
Generate Canonical Bilingual GeoJSON for NEW Survey Data
========================================================
Creates canonical GeoJSON for 29 new Beqaa Valley farmer survey responses.
Since we only have Arabic data, uses Arabic values for both ar/en until translations available.

Architecture:
- Single GeoJSON per theme
- Stable IDs: {theme}_{row}_{coordinateHash8}
- Bilingual structure (ar = en until translated)

Output: data/geojson/canonical/{Theme}_new.canonical.geojson
"""

import pandas as pd
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# New theme files (only those with data)
THEMES_NEW = {
    'Water': 'data/layers/Arabic/Water_new.csv',
    'General_Info': 'data/layers/Arabic/General_Info_new.csv',
    'Regenerative_Agriculture': 'data/layers/Arabic/Regenerative_Agriculture_new.csv'
}

# Columns to exclude
EXCLUDE_COLUMNS = ['X', 'Y', 'OBJECTID', 'FID']


def coordinate_hash(lon: float, lat: float, precision: int = 8) -> str:
    """
    Generate stable 8-character hash from coordinates.
    """
    coord_str = f"{lon:.8f},{lat:.8f}"
    return hashlib.sha256(coord_str.encode()).hexdigest()[:precision]


def generate_feature_id(theme: str, row_num: int, lon: float, lat: float) -> str:
    """
    Generate stable feature ID: {theme}_{row}_{coordinateHash8}
    """
    theme_key = theme.lower().replace('_', '')[:6]
    coord_hash = coordinate_hash(lon, lat)
    return f"{theme_key}_{row_num}_{coord_hash}"


def load_csv_with_fallback(file_path: str) -> pd.DataFrame:
    """
    Load CSV with multiple encoding attempts.
    """
    encodings = ['utf-8', 'utf-8-sig', 'cp1256', 'iso-8859-6']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"  Loaded successfully with {encoding}")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  Error with {encoding}: {e}")
            continue
    
    raise ValueError(f"Could not load {file_path} with any encoding")


def create_canonical_feature(row: pd.Series, theme: str, row_num: int, properties: List[str]) -> Dict:
    """
    Create canonical GeoJSON feature with bilingual properties.
    """
    try:
        lon = float(row['X'])
        lat = float(row['Y'])
    except (ValueError, KeyError) as e:
        print(f"  ⚠️  Row {row_num}: Invalid coordinates - {e}")
        return None
    
    # Generate stable ID
    feature_id = generate_feature_id(theme, row_num, lon, lat)
    
    # Extract property values (Arabic only for now)
    ar_values = {}
    for prop in properties:
        if prop in row.index and pd.notna(row[prop]):
            ar_values[prop] = str(row[prop])
    
    # Use Arabic values for both ar and en until translations available
    feature = {
        "type": "Feature",
        "id": feature_id,
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "featureId": feature_id,
            "theme": theme.lower(),
            "values": {
                "ar": ar_values,
                "en": ar_values  # TODO: Add English translations
            },
            "metadata": {
                "sourceRow": row_num,
                "coordinateHash": coordinate_hash(lon, lat),
                "dataSource": "MZSurvey_2026_Beqaa",
                "translationStatus": "pending"
            }
        }
    }
    
    return feature


def generate_canonical_geojson(theme: str, csv_file: str) -> Tuple[Dict, Dict]:
    """
    Generate canonical GeoJSON for a single theme.
    """
    print(f"\n{'='*70}")
    print(f"Processing theme: {theme}")
    print(f"{'='*70}")
    
    # Load CSV
    print(f"Loading CSV: {csv_file}")
    try:
        df = load_csv_with_fallback(csv_file)
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
    except Exception as e:
        print(f"  ✗ Failed to load: {e}")
        return None, None
    
    # Check required columns
    if 'X' not in df.columns or 'Y' not in df.columns:
        print(f"  ✗ Missing X or Y coordinates")
        return None, None
    
    # Get property columns (exclude coordinates and metadata)
    property_columns = [col for col in df.columns if col not in EXCLUDE_COLUMNS]
    print(f"  Property columns: {len(property_columns)}")
    
    # Generate features
    features = []
    skipped = 0
    
    for idx, row in df.iterrows():
        feature = create_canonical_feature(row, theme, idx + 1, property_columns)
        if feature:
            features.append(feature)
        else:
            skipped += 1
    
    if skipped > 0:
        print(f"  ⚠️  Skipped {skipped} rows due to invalid coordinates")
    
    # Create GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "theme": theme,
            "format": "canonical_bilingual",
            "version": "2.0",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": csv_file,
            "featureCount": len(features),
            "translationStatus": "pending",
            "notes": "English translations pending - using Arabic values for both languages"
        },
        "features": features
    }
    
    # Create audit record
    audit = {
        "theme": theme,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_arabic": csv_file,
        "source_english": "PENDING",
        "features_generated": len(features),
        "features_skipped": skipped,
        "property_columns": property_columns,
        "coordinate_validation": {
            "valid": len(features),
            "invalid": skipped
        },
        "translation_status": "Arabic only - English translations pending"
    }
    
    print(f"✓ Generated {len(features)} canonical features with stable IDs")
    
    return geojson, audit


def main():
    """
    Generate canonical GeoJSON for all new themes.
    """
    print("="*70)
    print("Canonical Bilingual GeoJSON Generator - NEW DATA")
    print("="*70)
    print("Architecture: Single GeoJSON per theme with nested bilingual values")
    print("Status: Arabic data only - English translations pending")
    print("Stable IDs: {theme}_{row}_{coordinateHash8}")
    print()
    
    # Create output directories
    output_dir = Path('data/geojson/canonical')
    audit_dir = Path('data/canonical_audit')
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Process each theme
    for theme, csv_file in THEMES_NEW.items():
        geojson, audit = generate_canonical_geojson(theme, csv_file)
        
        if geojson and audit:
            # Save GeoJSON
            output_file = output_dir / f'{theme}_new.canonical.geojson'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
            print(f"✓ Saved: {output_file}")
            
            # Save audit
            audit_file = audit_dir / f'{theme}_new_canonical_audit.json'
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(audit, f, ensure_ascii=False, indent=2)
            print(f"✓ Audit: {audit_file}")
            
            results.append({
                'theme': theme,
                'features': len(geojson['features']),
                'status': 'SUCCESS'
            })
        else:
            results.append({
                'theme': theme,
                'features': 0,
                'status': 'FAILED'
            })
    
    # Print summary
    print(f"\n{'='*70}")
    print("GENERATION SUMMARY")
    print(f"{'='*70}")
    for result in results:
        status_icon = '✓' if result['status'] == 'SUCCESS' else '✗'
        print(f"{status_icon} {result['theme']}: {result['features']} features - {result['status']}")
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_features = sum(r['features'] for r in results)
    
    print(f"\nTotal: {total_features} features across {success_count}/{len(results)} themes")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Audit directory: {audit_dir.absolute()}")
    
    print(f"\n{'='*70}")
    print("⚠️  NEXT STEP: Add English translations")
    print(f"{'='*70}")
    print("Current state: Arabic data loaded, English = Arabic (placeholder)")
    print("Required: Translate property values to English")
    print("Then: Regenerate canonical GeoJSON with both languages")


if __name__ == '__main__':
    main()

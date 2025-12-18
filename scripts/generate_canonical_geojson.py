"""
Generate Canonical Bilingual GeoJSON Files
==========================================
Merges Arabic and English CSV files into single canonical GeoJSON format
with stable feature IDs and nested bilingual property values.

Architecture:
- Single GeoJSON per theme (not separate AR/EN files)
- Stable IDs: {theme}_{row}_{coordinateHash8}
- Bilingual properties: values: {ar: {...}, en: {...}}
- Immutable workflow with audit trail

Output: data/geojson/canonical/{Theme}.canonical.geojson
"""

import pandas as pd
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Theme definitions with file mappings
THEMES = {
    'Water': {
        'ar_csv': 'data/layers/Arabic/Water_1.0.csv',
        'en_csv': 'data/layers/English/Water_1.0.en.csv'
    },
    'Energy': {
        'ar_csv': 'data/layers/Arabic/Energy_1.0.csv',
        'en_csv': 'data/layers/English/Energy_1.0.en.csv'
    },
    'Food': {
        'ar_csv': 'data/layers/Arabic/Food_1.0.csv',
        'en_csv': 'data/layers/English/Food_1.0.en.csv'
    },
    'General_Info': {
        'ar_csv': 'data/layers/Arabic/Generalinfo_1.0.csv',
        'en_csv': 'data/layers/English/Generalinfo_1.0.en.csv'
    },
    'Regenerative_Agriculture': {
        'ar_csv': 'data/layers/Arabic/Regenerative_1.0.csv',
        'en_csv': 'data/layers/English/Regenerative_1.0.en.csv'
    }
}

# Columns to exclude from properties (coordinate/metadata columns)
EXCLUDE_COLUMNS = ['X', 'Y', 'OBJECTID', 'FID']


def normalize_column_name(col: str) -> str:
    """Remove trailing colons and spaces from column names."""
    return col.rstrip(': ')


def generate_coordinate_hash(lon: float, lat: float, length: int = 8) -> str:
    """Generate deterministic hash from coordinates."""
    coord_str = f"{lon:.8f},{lat:.8f}"
    full_hash = hashlib.sha256(coord_str.encode()).hexdigest()
    return full_hash[:length]


def generate_stable_id(theme: str, row_idx: int, lon: float, lat: float) -> str:
    """
    Generate stable feature ID: {theme}_{row}_{coordinateHash8}
    Example: "Water_2_a3f8b9c1"
    """
    coord_hash = generate_coordinate_hash(lon, lat)
    return f"{theme}_{row_idx}_{coord_hash}"


def load_and_normalize_csv(csv_path: str) -> pd.DataFrame:
    """Load CSV and normalize column names."""
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df.columns = [normalize_column_name(col) for col in df.columns]
    return df


def merge_ar_en_row(ar_row: pd.Series, en_row: pd.Series, exclude_cols: List[str]) -> Dict:
    """
    Merge Arabic and English rows into canonical bilingual format.
    
    Returns:
    {
        "ar": {"القرية": "value", ...},
        "en": {"Village": "value", ...}
    }
    """
    ar_props = {}
    en_props = {}
    
    for col in ar_row.index:
        if col in exclude_cols:
            continue
        
        val_ar = ar_row[col]
        val_en = en_row[col] if col in en_row.index else None
        
        # Convert NaN to None for JSON serialization
        if pd.isna(val_ar):
            val_ar = None
        if pd.isna(val_en):
            val_en = None
        
        ar_props[col] = val_ar
        en_props[col] = val_en
    
    return {"ar": ar_props, "en": en_props}


def create_canonical_feature(theme: str, row_idx: int, ar_row: pd.Series, 
                             en_row: pd.Series, exclude_cols: List[str]) -> Dict:
    """
    Create canonical GeoJSON feature with stable ID and bilingual properties.
    
    Feature structure:
    {
        "type": "Feature",
        "id": "Water_2_a3f8b9c1",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "featureId": "Water_2_a3f8b9c1",
            "theme": "Water",
            "values": {
                "ar": {"القرية": "...", ...},
                "en": {"Village": "...", ...}
            }
        }
    }
    """
    # Extract coordinates
    lon = float(ar_row['X'])
    lat = float(ar_row['Y'])
    
    # Generate stable ID
    feature_id = generate_stable_id(theme, row_idx, lon, lat)
    
    # Merge bilingual properties
    values = merge_ar_en_row(ar_row, en_row, exclude_cols)
    
    # Build GeoJSON feature
    feature = {
        "type": "Feature",
        "id": feature_id,
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "featureId": feature_id,
            "theme": theme,
            "values": values
        }
    }
    
    return feature


def generate_canonical_geojson(theme: str, ar_csv_path: str, en_csv_path: str) -> Tuple[Dict, Dict]:
    """
    Generate canonical bilingual GeoJSON for a theme.
    
    Returns:
    - geojson: FeatureCollection
    - audit: Metadata and statistics
    """
    print(f"\n{'='*70}")
    print(f"Processing theme: {theme}")
    print(f"{'='*70}")
    
    # Load CSV files
    print(f"Loading Arabic CSV: {ar_csv_path}")
    df_ar = load_and_normalize_csv(ar_csv_path)
    print(f"  Rows: {len(df_ar)}, Columns: {len(df_ar.columns)}")
    
    print(f"Loading English CSV: {en_csv_path}")
    df_en = load_and_normalize_csv(en_csv_path)
    print(f"  Rows: {len(df_en)}, Columns: {len(df_en.columns)}")
    
    # Validate row counts match
    if len(df_ar) != len(df_en):
        raise ValueError(f"Row count mismatch: AR={len(df_ar)}, EN={len(df_en)}")
    
    # Generate features
    features = []
    for idx, (ar_row, en_row) in enumerate(zip(df_ar.itertuples(index=False), 
                                                 df_en.itertuples(index=False))):
        ar_series = pd.Series(ar_row._asdict())
        en_series = pd.Series(en_row._asdict())
        
        feature = create_canonical_feature(theme, idx, ar_series, en_series, EXCLUDE_COLUMNS)
        features.append(feature)
    
    # Build FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "theme": theme,
            "generatedAt": datetime.utcnow().isoformat() + 'Z',
            "featureCount": len(features),
            "sources": {
                "arabic": ar_csv_path,
                "english": en_csv_path
            }
        }
    }
    
    # Generate audit record
    audit = {
        "theme": theme,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "sources": {
            "arabic": {
                "path": ar_csv_path,
                "rows": len(df_ar),
                "columns": list(df_ar.columns)
            },
            "english": {
                "path": en_csv_path,
                "rows": len(df_en),
                "columns": list(df_en.columns)
            }
        },
        "output": {
            "featureCount": len(features),
            "stableIdFormat": "{theme}_{row}_{coordinateHash8}",
            "sampleIds": [f["id"] for f in features[:3]]
        }
    }
    
    print(f"✓ Generated {len(features)} canonical features with stable IDs")
    
    return geojson, audit


def main():
    """Generate all canonical GeoJSON files."""
    print("Canonical Bilingual GeoJSON Generator")
    print("=" * 70)
    print("Architecture: Single GeoJSON per theme with nested bilingual values")
    print("Stable IDs: {theme}_{row}_{coordinateHash8}")
    print()
    
    # Create output directories
    output_dir = Path('data/geojson/canonical')
    audit_dir = Path('data/canonical_audit')
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each theme
    results = []
    for theme, paths in THEMES.items():
        try:
            geojson, audit = generate_canonical_geojson(
                theme, 
                paths['ar_csv'], 
                paths['en_csv']
            )
            
            # Write GeoJSON
            output_path = output_dir / f"{theme}.canonical.geojson"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
            print(f"✓ Saved: {output_path}")
            
            # Write audit
            audit_path = audit_dir / f"{theme}_canonical_audit.json"
            with open(audit_path, 'w', encoding='utf-8') as f:
                json.dump(audit, f, ensure_ascii=False, indent=2)
            print(f"✓ Audit: {audit_path}")
            
            results.append({
                'theme': theme,
                'features': len(geojson['features']),
                'status': 'SUCCESS'
            })
            
        except Exception as e:
            print(f"✗ ERROR processing {theme}: {e}")
            results.append({
                'theme': theme,
                'features': 0,
                'status': f'FAILED: {e}'
            })
    
    # Summary report
    print(f"\n{'='*70}")
    print("GENERATION SUMMARY")
    print(f"{'='*70}")
    for result in results:
        status_icon = "✓" if result['status'] == 'SUCCESS' else "✗"
        print(f"{status_icon} {result['theme']}: {result['features']} features - {result['status']}")
    
    total_features = sum(r['features'] for r in results if r['status'] == 'SUCCESS')
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    
    print(f"\nTotal: {total_features} features across {success_count}/{len(THEMES)} themes")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Audit directory: {audit_dir.absolute()}")


if __name__ == '__main__':
    main()

"""
Data Inspection Tool
====================
Inspect canonical GeoJSON data to understand property structure and distributions.
"""

import json
import pandas as pd
from pathlib import Path
from collections import Counter


def inspect_canonical_data():
    """Inspect all canonical GeoJSON files."""
    
    data_dir = Path("data/geojson/canonical")
    themes = ['Water', 'Energy', 'Food', 'General_Info', 'Regenerative_Agriculture']
    
    print("=" * 80)
    print("CANONICAL DATA INSPECTION REPORT")
    print("=" * 80)
    
    for theme in themes:
        filepath = data_dir / f"{theme}.canonical.geojson"
        if not filepath.exists():
            print(f"\n⚠️  {theme}: File not found")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            geojson = json.load(f)
        
        features = geojson['features']
        print(f"\n{'=' * 80}")
        print(f"{theme.upper()} - {len(features)} features")
        print("=" * 80)
        
        # Get all property keys from first feature
        if features:
            sample_props = features[0]['properties']['values']['en']
            print(f"\nProperties ({len(sample_props)} total):")
            print("-" * 80)
            
            # Analyze each property
            for key in sorted(sample_props.keys()):
                values = []
                for feat in features:
                    val = feat['properties']['values']['en'].get(key)
                    if val is not None and val != '':
                        values.append(val)
                
                # Value distribution
                if values:
                    unique_count = len(set(values))
                    value_counts = Counter(values)
                    most_common = value_counts.most_common(3)
                    
                    print(f"\n{key}:")
                    print(f"  Non-null: {len(values)}/{len(features)} ({len(values)/len(features)*100:.1f}%)")
                    print(f"  Unique values: {unique_count}")
                    
                    if unique_count <= 10:
                        print(f"  Values: {list(value_counts.keys())}")
                    else:
                        print(f"  Top 3: {[v[0] for v in most_common]}")
                    
                    # Sample values
                    if unique_count <= 3:
                        for val, count in value_counts.items():
                            print(f"    - {val}: {count} ({count/len(values)*100:.1f}%)")
        
        # Show 2 complete sample records
        print(f"\n{'-' * 80}")
        print("SAMPLE RECORDS:")
        print("-" * 80)
        for i, feat in enumerate(features[:2]):
            print(f"\nRecord {i+1}:")
            props = feat['properties']['values']['en']
            for key, val in props.items():
                print(f"  {key}: {val}")


if __name__ == "__main__":
    inspect_canonical_data()

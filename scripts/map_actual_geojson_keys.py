"""
Map actual canonical GeoJSON property keys to their meanings.
Used to update property-schemas.js with correct keys.
"""

import pandas as pd

themes = {
    'Water': 'data/layers/English/Water_1.0.en.csv',
    'Energy': 'data/layers/English/Energy_1.0.en.csv',
    'Food': 'data/layers/English/Food_1.0.en.csv',
    'General': 'data/layers/English/Generalinfo_1.0.en.csv',
    'Regenerative': 'data/layers/English/Regenerative_1.0.en.csv'
}

for theme_name, csv_path in themes.items():
    print(f"\n{'='*70}")
    print(f"{theme_name} Theme")
    print('='*70)
    
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df.columns = [c.rstrip(': ') for c in df.columns]
    
    # Get namedtuple field names (what actually appears in GeoJSON)
    for row in df.itertuples(index=False):
        actual_keys = list(row._asdict().keys())
        break
    
    # Map to original column names
    print(f"Property Key Mappings (for property-schemas.js):\n")
    for i, col in enumerate(df.columns):
        if col in ['X', 'Y']:  # These are excluded from properties
            continue
        actual_key = actual_keys[i] if i < len(actual_keys) else col
        print(f"'{actual_key}': {{ en: '{col}', ar: '{col}' }},")

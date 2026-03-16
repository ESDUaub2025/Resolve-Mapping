#!/usr/bin/env python3
"""Map English and Arabic column names side by side."""

import pandas as pd
from pathlib import Path

csv_pairs = {
    'Energy': {
        'en': 'data/layers/English/Energy_1.0.en.csv',
        'ar': 'data/layers/Arabic/Energy_1.0.csv'
    },
    'Food': {
        'en': 'data/layers/English/Food_1.0.en.csv',
        'ar': 'data/layers/Arabic/Food_1.0.csv'
    },
    'General': {
        'en': 'data/layers/English/Generalinfo_1.0.en.csv',
        'ar': 'data/layers/Arabic/Generalinfo_1.0.csv'
    },
    'Regenerative': {
        'en': 'data/layers/English/Regenerative_1.0.en.csv',
        'ar': 'data/layers/Arabic/Regenerative_1.0.csv'
    },
    'Water': {
        'en': 'data/layers/English/Water_1.0.en.csv',
        'ar': 'data/layers/Arabic/Water_1.0.csv'
    }
}

for theme, paths in csv_pairs.items():
    print(f"\n{'='*80}")
    print(f"{theme.upper()}")
    print('='*80)
    
    df_en = pd.read_csv(paths['en'])
    df_ar = pd.read_csv(paths['ar'])
    
    # Get column names (they should match as Arabic column names)
    cols_en = list(df_en.columns)
    cols_ar = list(df_ar.columns)
    
    # Normalize: remove trailing colons and spaces
    cols_en_norm = [c.rstrip(':').strip() for c in cols_en]
    cols_ar_norm = [c.rstrip(':').strip() for c in cols_ar]
    
    print(f"{'No.':<4} {'Arabic Key':<40} {'English Label':<40}")
    print('-' * 84)
    
    for i in range(min(len(cols_ar_norm), len(cols_en_norm))):
        # Get the first row values to see example translations
        en_val = str(df_en.iloc[0, i])[:30] if len(df_en) > 0 else ''
        ar_val = str(df_ar.iloc[0, i])[:30] if len(df_ar) > 0 else ''
        
        print(f"{i+1:<4} {cols_ar_norm[i]:<40} {en_val:<40}")

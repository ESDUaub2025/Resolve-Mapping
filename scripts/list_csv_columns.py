#!/usr/bin/env python3
"""List all columns from English CSV files."""

import pandas as pd
from pathlib import Path

csv_files = {
    'Energy': 'data/layers/English/Energy_1.0.en.csv',
    'Food': 'data/layers/English/Food_1.0.en.csv',
    'General': 'data/layers/English/Generalinfo_1.0.en.csv',
    'Regenerative': 'data/layers/English/Regenerative_1.0.en.csv',
    'Water': 'data/layers/English/Water_1.0.en.csv'
}

for theme, csv_path in csv_files.items():
    print(f"\n{'='*60}")
    print(f"{theme.upper()} COLUMNS:")
    print('='*60)
    df = pd.read_csv(csv_path)
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")

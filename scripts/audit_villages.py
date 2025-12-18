#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract all unique village names from Arabic CSV files"""

import pandas as pd
import os

data_dir = 'data/layers/Arabic'
themes = ['Energy_1.0.csv', 'Food_1.0.csv', 'Generalinfo_1.0.csv', 'Regenerative_1.0.csv', 'Water_1.0.csv']

villages = set()

for theme in themes:
    filepath = os.path.join(data_dir, theme)
    df = pd.read_csv(filepath, encoding='utf-8')
    village_col = df['القرية:'].str.strip()
    villages.update(village_col.dropna().unique())

# Sort and print
for village in sorted(villages):
    print(village)

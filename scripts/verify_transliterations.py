#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Comprehensive verification of village name transliterations"""

import pandas as pd
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYERS_EN = ROOT / 'data' / 'layers' / 'English'
LAYERS_AR = ROOT / 'data' / 'layers' / 'Arabic'

# Themes to check
THEMES = {
    'Energy': ('Energy_1.0.csv', 'Energy_1.0.en.csv'),
    'Food': ('Food_1.0.csv', 'Food_1.0.en.csv'),
    'General_Info': ('Generalinfo_1.0.csv', 'Generalinfo_1.0.en.csv'),
    'Regenerative_Agriculture': ('Regenerative_1.0.csv', 'Regenerative_1.0.en.csv'),
    'Water': ('Water_1.0.csv', 'Water_1.0.en.csv')
}

print("\n" + "="*80)
print("VILLAGE NAME TRANSLITERATION VERIFICATION")
print("="*80)

# Check for problem translations
PROBLEM_TRANSLATIONS = ['My lady', 'towers', 'سيدتي', 'أبراج']

for theme_name, (ar_file, en_file) in THEMES.items():
    print(f"\n📊 {theme_name}:")
    
    # Read Arabic version
    ar_path = LAYERS_AR / ar_file
    ar_df = pd.read_csv(ar_path, encoding='utf-8')
    
    # Read English version
    en_path = LAYERS_EN / en_file
    en_df = pd.read_csv(en_path, encoding='utf-8')
    
    # Get village columns
    ar_villages = ar_df['القرية:'].str.strip().dropna().unique()
    en_villages = en_df['القرية:'].str.strip().dropna().unique()
    
    print(f"   Arabic villages: {len(ar_villages)}")
    print(f"   English villages: {len(en_villages)}")
    
    # Check for problem translations
    problems = [v for v in en_villages if v in PROBLEM_TRANSLATIONS]
    if problems:
        print(f"   ⚠️  PROBLEM TRANSLATIONS FOUND: {problems}")
    else:
        print(f"   ✅ No literal translations detected")
    
    # Show specific villages mentioned
    mrosti_in_ar = 'مرستي' in ar_villages or 'مرستى' in ar_villages
    mrosti_in_en = any('Mrosti' in v or 'Mresty' in v for v in en_villages)
    
    barja_in_ar = 'برجا' in ar_villages
    barja_in_en = 'Barja' in en_villages
    
    if mrosti_in_ar:
        if mrosti_in_en:
            print(f"   ✅ مرستي → Mrosti (correct)")
        else:
            print(f"   ⚠️  مرستي found in Arabic but NOT transliterated in English")
    
    if barja_in_ar:
        if barja_in_en:
            print(f"   ✅ برجا → Barja (correct)")
        else:
            print(f"   ⚠️  برجا found in Arabic but NOT transliterated in English")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80 + "\n")

# Final comprehensive check
print("\n🔍 Comprehensive Data Search:")
all_problems_found = []

for theme_name, (ar_file, en_file) in THEMES.items():
    en_path = LAYERS_EN / en_file
    with open(en_path, 'r', encoding='utf-8') as f:
        content = f.read()
        for problem in PROBLEM_TRANSLATIONS:
            if problem in content:
                all_problems_found.append(f"{theme_name}: '{problem}'")

if all_problems_found:
    print(f"❌ PROBLEM TRANSLATIONS STILL EXIST:")
    for problem in all_problems_found:
        print(f"   - {problem}")
else:
    print("✅ ZERO LITERAL TRANSLATIONS FOUND - ALL CLEAN!")

print("\n" + "="*80 + "\n")

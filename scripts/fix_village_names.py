#!/usr/bin/env python3
"""Fix village names in English CSV files - they should not be translated.

This script:
1. Reads village names from Arabic CSV files (source of truth)
2. Updates English CSV files with original Arabic village names
3. Maintains all other data integrity
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LAYERS_EN = ROOT / 'data' / 'layers' / 'English'
LAYERS_AR = ROOT / 'data' / 'layers' / 'Arabic'

# Theme mappings
THEMES = {
    'Energy': {
        'en_file': 'Energy_1.0.en.csv',
        'ar_file': 'Energy_1.0.csv',
        'village_col_en': 'القرية:',
        'village_col_ar': 'القرية:'
    },
    'Food': {
        'en_file': 'Food_1.0.en.csv',
        'ar_file': 'Food_1.0.csv',
        'village_col_en': 'القرية:',
        'village_col_ar': 'القرية:'
    },
    'General_Info': {
        'en_file': 'Generalinfo_1.0.en.csv',
        'ar_file': 'Generalinfo_1.0.csv',
        'village_col_en': 'القرية:',
        'village_col_ar': 'القرية:'
    },
    'Regenerative_Agriculture': {
        'en_file': 'Regenerative_1.0.en.csv',
        'ar_file': 'Regenerative_1.0.csv',
        'village_col_en': 'القرية:',
        'village_col_ar': 'القرية:'
    },
    'Water': {
        'en_file': 'Water_1.0.en.csv',
        'ar_file': 'Water_1.0.csv',
        'village_col_en': 'القرية:',
        'village_col_ar': 'القرية:'
    }
}


def fix_village_names(theme_name, theme_config):
    """Fix village names for a single theme."""
    print(f"\n{'='*60}")
    print(f"Fixing village names: {theme_name}")
    print(f"{'='*60}")
    
    # Read files
    en_path = LAYERS_EN / theme_config['en_file']
    ar_path = LAYERS_AR / theme_config['ar_file']
    
    if not en_path.exists():
        print(f"⚠️  English file not found: {en_path.name}")
        return False
    
    if not ar_path.exists():
        print(f"⚠️  Arabic file not found: {ar_path.name}")
        return False
    
    print(f"Reading: {en_path.name}")
    df_en = pd.read_csv(en_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
    df_en.columns = [c.strip() for c in df_en.columns]
    
    print(f"Reading: {ar_path.name}")
    df_ar = pd.read_csv(ar_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
    df_ar.columns = [c.strip() for c in df_ar.columns]
    
    # Check row counts match
    if len(df_en) != len(df_ar):
        print(f"❌ ERROR: Row count mismatch!")
        print(f"   English: {len(df_en)} rows")
        print(f"   Arabic: {len(df_ar)} rows")
        return False
    
    # Get village column names
    village_col_en = theme_config['village_col_en']
    village_col_ar = theme_config['village_col_ar']
    
    if village_col_en not in df_en.columns:
        print(f"❌ ERROR: Village column '{village_col_en}' not found in English CSV")
        print(f"   Available columns: {', '.join(df_en.columns)}")
        return False
    
    if village_col_ar not in df_ar.columns:
        print(f"❌ ERROR: Village column '{village_col_ar}' not found in Arabic CSV")
        print(f"   Available columns: {', '.join(df_ar.columns)}")
        return False
    
    # Copy village names from Arabic to English
    print(f"\nCopying village names from Arabic to English...")
    original_villages = df_en[village_col_en].tolist()
    arabic_villages = df_ar[village_col_ar].tolist()
    
    df_en[village_col_en] = arabic_villages
    
    # Show sample changes
    print(f"\nSample changes (first 5 rows):")
    for i in range(min(5, len(df_en))):
        if original_villages[i] != arabic_villages[i]:
            print(f"  Row {i+2}: '{original_villages[i]}' → '{arabic_villages[i]}'")
        else:
            print(f"  Row {i+2}: '{arabic_villages[i]}' (unchanged)")
    
    # Create backup
    backup_path = en_path.with_suffix('.csv.backup')
    if not backup_path.exists():
        print(f"\nCreating backup: {backup_path.name}")
        df_en_original = pd.read_csv(en_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
        df_en_original.to_csv(backup_path, index=False, encoding='utf-8-sig')
    
    # Save updated English CSV
    print(f"Saving: {en_path.name}")
    df_en.to_csv(en_path, index=False, encoding='utf-8-sig')
    
    print(f"✓ Success! Fixed {len(df_en)} rows")
    return True


def main():
    print("\n" + "="*60)
    print("Village Name Fixer")
    print("Restores original Arabic village names in English CSV files")
    print("="*60)
    
    success_count = 0
    error_count = 0
    
    for theme_name, theme_config in THEMES.items():
        try:
            if fix_village_names(theme_name, theme_config):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"\n❌ Error fixing {theme_name}: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✓ Successfully fixed: {success_count} themes")
    if error_count > 0:
        print(f"❌ Failed: {error_count} themes")
    print("="*60)
    print("\nNext step: Run csvs_to_geojson_complete.py to regenerate GeoJSON files")
    print("  python scripts/csvs_to_geojson_complete.py --all")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

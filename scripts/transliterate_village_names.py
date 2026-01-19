#!/usr/bin/env python3
"""
Transliterate Lebanese village names from Arabic to English (phonetic).
Uses official transliterations based on Lebanese geography and pronunciation.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LAYERS_EN = ROOT / 'data' / 'layers' / 'English'
LAYERS_AR = ROOT / 'data' / 'layers' / 'Arabic'

# Official transliterations of Lebanese villages in Mount Lebanon, Chouf District & Beqaa Valley
# Based on phonetic pronunciation and official Lebanese naming conventions
# Updated January 2026 with 11 new Beqaa Valley villages
VILLAGE_TRANSLITERATIONS = {
    # Beqaa Valley villages (NEW - January 2026)
    'الفاكهة': 'Al-Fakiha',
    'اللبوة': 'Al-Labweh',
    'تربل': 'Tarbol',
    'حارة الفيكاني': 'Haret Al-Faykani',
    'دلهامية': 'Dalhamieh',
    'رياق': 'Rayak',
    'زحلة': 'Zahle',
    'علي النهري': 'Ali Al-Nahri',
    'ماسما': 'Masma',
    'مشغرة': 'Machghara',
    'نبي شيت': 'Nabi Chit',
    
    # Mount Lebanon & Chouf District (existing)
    'الباروك': 'Al-Barouk',
    'البيره': 'Al-Bireh',
    'البيرة': 'Al-Bireh',
    'الجاهليه': 'Al-Jahiliyeh',
    'الجاهلية': 'Al-Jahiliyeh',
    'الدامور': 'Damour',
    'الدبيه': 'Al-Debbiyeh',
    'الدبية': 'Al-Debbiyeh',
    'السعديات': 'Al-Saadiyat',
    'السمقانيه': 'Al-Simqaniyeh',
    'السمقانية': 'Al-Simqaniyeh',
    'الكحلونيه': 'Al-Kahlouniyeh',
    'الكحلونية': 'Al-Kahlouniyeh',
    'المشرف': 'Al-Moshref',
    'المطله': 'Al-Mtalleh',
    'المطلة': 'Al-Mtalleh',
    'المغيزيه': 'Al-Mughayziyeh',
    'المغيزية': 'Al-Mughayziyeh',
    'الورهانيه': 'Al-Warhaniyeh',
    'الورهانية': 'Al-Warhaniyeh',
    'ورهانيه': 'Warhaniyeh',
    'المختارة': 'Al-Mokhtara',
    'باتر': 'Bater',
    'بتلون': 'Btalloun',
    'برجا': 'Barja',
    'بريح': 'Breih',
    'بشتفين': 'Bshtfine',
    'بطمه': 'Btameh',
    'بطمة': 'Btameh',
    'بعذران': 'Baatharan',
    'بعقلين': 'Baaqline',
    'بكيفا': 'Bkifa',
    'جديده الشوف': 'Jadideh El Chouf',
    'جديدة الشوف': 'Jadideh El Chouf',
    'حاره جندل الشوف': 'Haret Jandal El Chouf',
    'حارة جندل الشوف': 'Haret Jandal El Chouf',
    'خربه بسري': 'Khirbet Bosri',
    'خربة بسري': 'Khirbet Bosri',
    'خريبه الشوف': 'Khraybeh El Chouf',
    'خريبة الشوف': 'Khraybeh El Chouf',
    'داريا الشوف': 'Daraya El Chouf',
    'دميت الشوف': 'Dmit El Chouf',
    'دير القمر': 'Deir El Qamar',
    'دير دوريت': 'Deir Dourit',
    'ديردوريت': 'Deir Dourit',
    'ديربابا': 'Deir Baba',
    'ديربآبا': 'Deir Baba',
    'شارون': 'Charoun',
    'شحيم': 'Chahim',
    'شواليق دير القمر': 'Chawalik Deir El Qamar',
    'عانوت': 'Aanout',
    'عترين': 'Atrine',
    'علمان': 'Aalman',
    'عماطور': 'Ammatour',
    'عين زحلتا': 'Ain Zahlta',
    'عين قاني': 'Ain Qani',
    'عين وزين': 'Ain W Zain',
    '  عين وزين': 'Ain W Zain',
    'غريفه': 'Gharifeh',
    'غريفة': 'Gharifeh',
    'كترمايا الشوف': 'Ktermaya El Chouf',
    'كحلونيه الشوف': 'Kahlouniyeh El Chouf',
    'كحلونية الشوف': 'Kahlouniyeh El Chouf',
    'كفرحيم': 'Kfarhaym',
    'كفرفاقود': 'Kfarfakoud',
    'كفرفاقود الشوف': 'Kfarfakoud El Chouf',
    'كفرنبرخ': 'Kfarnabrakh',
    'مجدل المعوش': 'Majdel El Meouch',
    'مرستي': 'Mrosti',
    'مرستى': 'Mrosti',
    'مزبود': 'Mazboud',
    'مزرعه الشوف': 'Mazraat El Chouf',
    'مزرعة الشوف': 'Mazraat El Chouf',
    'مزموره': 'Mazmoura',
    'مزمورة': 'Mazmoura',
    'معاصر الشوف': 'Maaser El Chouf',
    'نيحا الشوف': 'Niha El Chouf',
    'باروك': 'Barouk',
    'مختاره': 'Mokhtara',
    'مزرعهالشوف': 'Mazraat El Chouf',
    'مزرعةالشوف': 'Mazraat El Chouf',
    'بريح الشوف': 'Breih El Chouf',
    'ورهانية': 'Warhaniyeh'
}

# Theme configuration
THEMES = {
    'Energy': {
        'en_file': 'Energy_1.0.en.csv',
        'ar_file': 'Energy_1.0.csv',
        'village_col': 'القرية:'
    },
    'Food': {
        'en_file': 'Food_1.0.en.csv',
        'ar_file': 'Food_1.0.csv',
        'village_col': 'القرية:'
    },
    'General_Info': {
        'en_file': 'Generalinfo_1.0.en.csv',
        'ar_file': 'Generalinfo_1.0.csv',
        'village_col': 'القرية:'
    },
    'Regenerative_Agriculture': {
        'en_file': 'Regenerative_1.0.en.csv',
        'ar_file': 'Regenerative_1.0.csv',
        'village_col': 'القرية:'
    },
    'Water': {
        'en_file': 'Water_1.0.en.csv',
        'ar_file': 'Water_1.0.csv',
        'village_col': 'القرية:'
    }
}


def transliterate_village(arabic_name):
    """Transliterate Arabic village name to English."""
    # Clean the name
    name = arabic_name.strip()
    
    # Try exact match first
    if name in VILLAGE_TRANSLITERATIONS:
        return VILLAGE_TRANSLITERATIONS[name]
    
    # Try without leading/trailing spaces
    name_clean = ' '.join(name.split())
    if name_clean in VILLAGE_TRANSLITERATIONS:
        return VILLAGE_TRANSLITERATIONS[name_clean]
    
    # If no match found, return original with warning
    print(f"  ⚠️  Unknown village: '{name}' (keeping as-is)")
    return name


def transliterate_theme(theme_name, theme_config):
    """Transliterate village names for a single theme."""
    print(f"\n{'='*60}")
    print(f"Transliterating: {theme_name}")
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
    
    # Get village column
    village_col = theme_config['village_col']
    
    if village_col not in df_en.columns:
        print(f"❌ ERROR: Village column '{village_col}' not found in English CSV")
        return False
    
    if village_col not in df_ar.columns:
        print(f"❌ ERROR: Village column '{village_col}' not found in Arabic CSV")
        return False
    
    # Transliterate village names
    print(f"\nTransliterating village names...")
    original_villages_en = df_en[village_col].tolist()
    arabic_villages = df_ar[village_col].tolist()
    transliterated_villages = [transliterate_village(v) for v in arabic_villages]
    
    # Update English CSV
    df_en[village_col] = transliterated_villages
    
    # Show changes
    print(f"\nChanges (first 10 rows):")
    unique_changes = {}
    for i in range(len(df_en)):
        ar_name = arabic_villages[i]
        en_name = transliterated_villages[i]
        if ar_name not in unique_changes:
            unique_changes[ar_name] = en_name
    
    for ar_name, en_name in list(unique_changes.items())[:10]:
        print(f"  '{ar_name}' → '{en_name}'")
    
    if len(unique_changes) > 10:
        print(f"  ... and {len(unique_changes) - 10} more unique villages")
    
    # Create backup
    backup_path = en_path.with_suffix('.csv.pre_transliterate_backup')
    if not backup_path.exists():
        print(f"\nCreating backup: {backup_path.name}")
        df_en_original = pd.read_csv(en_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
        df_en_original.to_csv(backup_path, index=False, encoding='utf-8-sig')
    
    # Save updated English CSV
    print(f"Saving: {en_path.name}")
    df_en.to_csv(en_path, index=False, encoding='utf-8-sig')
    
    print(f"✓ Success! Transliterated {len(df_en)} rows ({len(unique_changes)} unique villages)")
    return True


def main():
    print("\n" + "="*60)
    print("Lebanese Village Name Transliterator")
    print("Arabic → English (Phonetic/Official)")
    print("="*60)
    
    success_count = 0
    error_count = 0
    
    for theme_name, theme_config in THEMES.items():
        try:
            if transliterate_theme(theme_name, theme_config):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"\n❌ Error transliterating {theme_name}: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✓ Successfully transliterated: {success_count} themes")
    if error_count > 0:
        print(f"❌ Failed: {error_count} themes")
    print("="*60)
    print("\nNext step: Regenerate GeoJSON files")
    print("  python scripts/csvs_to_geojson_complete.py --all")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

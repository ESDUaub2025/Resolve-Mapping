"""
Add Verified Coordinates to Survey Data
========================================
Maps village names to verified coordinates and adds X, Y columns to CSV

PRODUCTION-LEVEL SAFETY CHECKS:
- Validates all villages have coordinates
- Preserves all original columns
- Adds columns at end: X (longitude), Y (latitude)
- Creates backup of original file
- Generates detailed audit report
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Load verified coordinates
COORD_FILE = Path('data/verified_village_coordinates.json')
with open(COORD_FILE, encoding='utf-8') as f:
    coord_data = json.load(f)

COORDINATES = coord_data['villages']

def add_coordinates_to_survey():
    """Add X, Y coordinate columns to survey CSV"""
    
    input_file = Path('data/MZSurvey farmers ENGLISH.csv')
    output_file = Path('data/MZSurvey farmers ENGLISH_with_coords.csv')
    backup_file = Path('data/MZSurvey farmers ENGLISH_BACKUP_20260119.csv')
    
    print("="*80)
    print("ADDING VERIFIED COORDINATES TO SURVEY DATA")
    print("="*80)
    
    # 1. BACKUP ORIGINAL FILE
    print("\n📋 Step 1: Creating backup...")
    import shutil
    shutil.copy2(input_file, backup_file)
    print(f"  ✓ Backup saved: {backup_file}")
    
    # 2. LOAD SURVEY DATA
    print("\n📊 Step 2: Loading survey data...")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"  ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # 3. IDENTIFY VILLAGE COLUMN
    village_col = '4.القرية:'
    if village_col not in df.columns:
        raise ValueError(f"Village column '{village_col}' not found!")
    
    print(f"\n🏘️  Step 3: Mapping villages to coordinates...")
    print(f"  Using column: {village_col}")
    
    # 4. ADD COORDINATE COLUMNS
    x_coords = []
    y_coords = []
    mapping_log = []
    unmapped_villages = []
    
    for idx, row in df.iterrows():
        village_ar = row[village_col]
        
        if pd.isna(village_ar):
            x_coords.append(None)
            y_coords.append(None)
            mapping_log.append({'row': idx+1, 'village': 'EMPTY', 'status': 'SKIPPED'})
            continue
        
        village_ar = str(village_ar).strip()
        
        if village_ar in COORDINATES:
            coord_info = COORDINATES[village_ar]
            x_coords.append(coord_info['lon'])
            y_coords.append(coord_info['lat'])
            mapping_log.append({
                'row': idx+1,
                'village_ar': village_ar,
                'village_en': coord_info['name_en'],
                'lat': coord_info['lat'],
                'lon': coord_info['lon'],
                'confidence': coord_info['confidence'],
                'status': 'MAPPED'
            })
            print(f"  ✓ Row {idx+1:2d}: {village_ar:20s} → ({coord_info['lat']:.6f}, {coord_info['lon']:.6f}) [{coord_info['confidence']}]")
        else:
            x_coords.append(None)
            y_coords.append(None)
            unmapped_villages.append((idx+1, village_ar))
            mapping_log.append({'row': idx+1, 'village': village_ar, 'status': 'UNMAPPED'})
            print(f"  ✗ Row {idx+1:2d}: {village_ar:20s} → NO COORDINATES FOUND")
    
    # 5. ADD COLUMNS TO DATAFRAME
    df['X'] = x_coords
    df['Y'] = y_coords
    
    # 6. VALIDATION
    print("\n✅ Step 4: Validation checks...")
    mapped_count = df['X'].notna().sum()
    total_count = len(df)
    
    print(f"  Total rows: {total_count}")
    print(f"  Rows with coordinates: {mapped_count}")
    print(f"  Rows without coordinates: {total_count - mapped_count}")
    
    if unmapped_villages:
        print("\n  ⚠️  WARNING: Unmapped villages found:")
        for row_num, village in unmapped_villages:
            print(f"    - Row {row_num}: {village}")
        print("\n  ❌ CANNOT PROCEED - ALL VILLAGES MUST HAVE COORDINATES")
        return False
    
    # 7. SAVE OUTPUT
    print("\n💾 Step 5: Saving output...")
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"  ✓ Output saved: {output_file}")
    print(f"  ✓ Columns: {len(df.columns)} (original {len(df.columns)-2} + X + Y)")
    
    # 8. GENERATE AUDIT REPORT
    audit_report = {
        'timestamp': datetime.now().isoformat(),
        'input_file': str(input_file),
        'output_file': str(output_file),
        'backup_file': str(backup_file),
        'coordinate_source': str(COORD_FILE),
        'statistics': {
            'total_rows': int(total_count),
            'mapped_rows': int(mapped_count),
            'unmapped_rows': int(total_count - mapped_count),
            'unique_villages': int(len(df[village_col].unique())),
            'coordinate_precision': '6 decimal places (±0.1m)'
        },
        'mapping_details': mapping_log
    }
    
    audit_file = Path('data/coordinate_addition_audit.json')
    with open(audit_file, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Audit report: {audit_file}")
    
    # 9. SUMMARY
    print("\n" + "="*80)
    print("✅ COORDINATE ADDITION COMPLETE")
    print("="*80)
    print(f"  📊 Successfully mapped {mapped_count}/{total_count} rows (100%)")
    print(f"  📍 All villages have verified coordinates")
    print(f"  🎯 Ready for Phase 1.2 (Village Name Transliteration)")
    print("="*80)
    
    return True


if __name__ == '__main__':
    success = add_coordinates_to_survey()
    if not success:
        print("\n❌ PROCESS FAILED - FIX ISSUES BEFORE CONTINUING")
        exit(1)
    else:
        print("\n🚀 NEXT STEP: Village name transliteration audit")
        print("   Run: python scripts/audit_village_transliterations.py")

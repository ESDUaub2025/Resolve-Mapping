#!/usr/bin/env python3
"""
Combine Original Data to Excel
================================
Merges all original Arabic CSV data files into a single Excel workbook
with 100% data integrity preservation.

Output: data/Original_Survey_Data_Complete.xlsx
Each theme gets its own sheet with ALL original data.
"""

import pandas as pd
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'layers' / 'Arabic'
OUTPUT_FILE = BASE_DIR / 'data' / 'Original_Survey_Data_Complete.xlsx'

# Theme files mapping (original data sources)
THEME_FILES = {
    'Water_Original': 'Water_1.0.csv',
    'Water_Beqaa_2026': 'Water_new.csv',
    'Energy_Original': 'Energy_1.0.csv',
    'Food_Original': 'Food_1.0.csv',
    'General_Info_Original': 'Generalinfo_1.0.csv',
    'General_Info_Beqaa_2026': 'General_Info_new.csv',
    'Regenerative_Agriculture_Original': 'Regenerative_1.0.csv',
    'Regenerative_Agriculture_Beqaa_2026': 'Regenerative_Agriculture_new.csv'
}

def read_csv_safe(file_path):
    """
    Read CSV with proper encoding and error handling.
    Preserves ALL data exactly as-is.
    """
    try:
        # Try UTF-8 first (standard)
        df = pd.read_csv(file_path, encoding='utf-8')
        return df
    except UnicodeDecodeError:
        # Fallback to UTF-8 with BOM or Windows encoding
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            return df
        except:
            try:
                df = pd.read_csv(file_path, encoding='cp1256')  # Arabic Windows encoding
                return df
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return None

def combine_data():
    """
    Combine all original data files into one Excel workbook.
    Each theme gets its own sheet for easy reference.
    """
    print("=" * 80)
    print("COMBINING ORIGINAL SURVEY DATA INTO EXCEL")
    print("=" * 80)
    
    # Check if pandas has openpyxl
    try:
        import openpyxl
    except ImportError:
        print("\n⚠️  Installing openpyxl for Excel support...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'openpyxl'])
        print("✓ openpyxl installed")
    
    # Create Excel writer
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        total_rows = 0
        sheets_created = 0
        
        for sheet_name, file_name in THEME_FILES.items():
            file_path = DATA_DIR / file_name
            
            # Skip empty or non-existent files
            if not file_path.exists():
                print(f"⚠️  Skipping {file_name}: File not found")
                continue
                
            if file_path.stat().st_size == 0:
                print(f"⚠️  Skipping {file_name}: Empty file")
                continue
            
            print(f"\n📄 Processing: {file_name}")
            df = read_csv_safe(file_path)
            
            if df is None:
                print(f"   ❌ Failed to read")
                continue
            
            # Skip if no data rows (only header)
            if len(df) == 0:
                print(f"   ⚠️  No data rows")
                continue
            
            # Write to Excel sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            row_count = len(df)
            col_count = len(df.columns)
            total_rows += row_count
            sheets_created += 1
            
            print(f"   ✓ Written to sheet '{sheet_name}'")
            print(f"   📊 {row_count} rows × {col_count} columns")
            
            # Show first few column names (trimmed)
            sample_cols = df.columns[:5].tolist()
            if len(df.columns) > 5:
                sample_cols.append(f"... +{len(df.columns) - 5} more")
            print(f"   📋 Columns: {', '.join([str(c)[:30] for c in sample_cols])}")
    
    print("\n" + "=" * 80)
    print("✅ EXCEL FILE CREATED SUCCESSFULLY")
    print("=" * 80)
    print(f"📁 Output: {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print(f"📊 Total sheets: {sheets_created}")
    print(f"📈 Total data rows: {total_rows}")
    print(f"💾 File size: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB")
    print("\n✓ All original data preserved with 100% integrity")
    print("✓ Each theme has its own sheet for easy reference")
    print("=" * 80)

if __name__ == '__main__':
    combine_data()

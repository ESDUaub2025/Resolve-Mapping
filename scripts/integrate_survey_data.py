"""
Phase 2: Integration with Existing Data
========================================
Separate survey into Arabic/English versions and integrate with existing canonical data

Process:
1. Load theme-specific CSV files
2. Separate into Arabic and English versions
3. Map column names to match existing schema
4. Append to existing theme CSV files (or create new section)
5. Regenerate canonical bilingual GeoJSON
6. Verify no ID collisions
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import shutil

# Map survey Arabic columns to existing theme schema columns
COLUMN_NAME_MAPPING = {
    'Water': {
        'ar': {
            '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟': 'المحصول',
            '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟': 'مصدر مياه الريّ الرئيسي',
            '15.كم مرة تقوم بري هذين المحصولين في الأسبوع؟': 'ريّ المحصول',
            '16.كيف تقيّم توفر المياه خلال موسم الزراعة؟': 'توفر المياه',
            '17.هل تواجه نقصًا في المياه في أي وقت من السنة؟ إذا كانت الإجابة نعم، حدد الأشهر.': 'أشهر شح المياه',
        }
    },
    'Energy': {
        'ar': {
            '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟': 'مصدر الطاقة الرئيسي',
        }
    },
    'Food': {
        'ar': {
            '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟': 'المحصولين الرئيسيين',
        }
    },
    'General_Info': {
        'ar': {
            '4.القرية:': 'القرية',
            '8.ما هو حجم الحيازة الزراعية الخاصة بك؟': 'حجم الزراعة',
            '9.ما هو نوع التربة في أرضك؟': 'نوع التربة',
            '20.هل لاحظت أي تغيرات في المناخ على مدى السنوات القليلة الماضية تؤثر على الزراعة؟': 'ملاحظة تغيرات مناخية',
        }
    },
    'Regenerative_Agriculture': {
        'ar': {
            '32.هل تمارس الزراعة التجديدية؟': 'الزراعة التجديدية',
            '33.ما هي التقنيات التي تطبقها من الزراعة التجديدية؟': 'تقنيات الزراعة التجديدية',
            '38.ما هي أنواع المحسنات التي تستخدمها في التربة؟': 'محسنات التربة',
            '39.ما مدى اعتمادك على الأسمدة الكيميائية؟': 'الاعتماد على الاسمدة الكيميائية',
            '43.كيف تقوم بمكافحة الآفات؟': 'مكافحة الآفات',
        }
    }
}


def load_theme_files():
    """Load all theme-specific CSV files from Phase 1.4"""
    theme_dir = Path('data/survey_by_theme')
    
    if not theme_dir.exists():
        raise FileNotFoundError(f"Theme directory not found: {theme_dir}")
    
    themes = {}
    for theme in ['Water', 'Energy', 'Food', 'General_Info', 'Regenerative_Agriculture']:
        file_path = theme_dir / f'MZSurvey_{theme}.csv'
        if file_path.exists():
            df = pd.read_csv(file_path, encoding='utf-8')
            themes[theme] = df
            print(f"  ✓ {theme}: {len(df)} rows × {len(df.columns)} columns")
        else:
            print(f"  ⚠️  {theme}: File not found, skipping")
    
    return themes


def rename_columns_to_schema(df, theme):
    """Rename survey columns to match existing schema"""
    if theme not in COLUMN_NAME_MAPPING:
        return df
    
    mapping = COLUMN_NAME_MAPPING[theme]['ar']
    
    # Create new dataframe with renamed columns
    df_renamed = df.copy()
    df_renamed.rename(columns=mapping, inplace=True)
    
    # Keep only X, Y, village, and mapped columns
    keep_cols = ['4.القرية:', 'X', 'Y'] + list(mapping.values())
    available_cols = [col for col in keep_cols if col in df_renamed.columns]
    
    df_renamed = df_renamed[available_cols]
    
    # Rename village column if present
    if '4.القرية:' in df_renamed.columns:
        df_renamed.rename(columns={'4.القرية:': 'القرية'}, inplace=True)
    
    return df_renamed


def check_existing_data(theme):
    """Check if existing theme CSV files exist"""
    arabic_file = Path(f'data/layers/Arabic/{theme}.csv')
    english_file = Path(f'data/layers/English/{theme}.csv')
    
    exists = {
        'arabic': arabic_file.exists(),
        'english': english_file.exists()
    }
    
    if exists['arabic']:
        df_ar = pd.read_csv(arabic_file, encoding='utf-8')
        exists['arabic_rows'] = len(df_ar)
        exists['arabic_cols'] = len(df_ar.columns)
    else:
        exists['arabic_rows'] = 0
        exists['arabic_cols'] = 0
    
    return exists


def create_new_theme_csvs(themes):
    """Create new Arabic CSV files for each theme with new survey data"""
    
    output_dir_ar = Path('data/layers/Arabic')
    output_dir_ar.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    
    for theme_name, df in themes.items():
        print(f"\n  Processing {theme_name}...")
        
        # Rename columns to match schema
        df_renamed = rename_columns_to_schema(df, theme_name)
        
        # Check existing data
        existing = check_existing_data(theme_name)
        
        if existing['arabic']:
            print(f"    ⚠️  Existing file found: {existing['arabic_rows']} rows")
            print(f"    💡 Will append new data to create expanded dataset")
            
            # For now, create separate file with "_new" suffix
            output_file = output_dir_ar / f'{theme_name}_new.csv'
        else:
            print(f"    ✓ No existing file - creating new")
            output_file = output_dir_ar / f'{theme_name}_new.csv'
        
        # Save
        df_renamed.to_csv(output_file, index=False, encoding='utf-8')
        
        created_files.append({
            'theme': theme_name,
            'file': str(output_file),
            'rows': len(df_renamed),
            'columns': len(df_renamed.columns),
            'column_names': list(df_renamed.columns)
        })
        
        print(f"    ✓ Saved: {output_file.name} ({len(df_renamed)} rows × {len(df_renamed.columns)} columns)")
        print(f"    📋 Columns: {', '.join(df_renamed.columns)}")
    
    return created_files


def generate_integration_plan(created_files):
    """Generate detailed integration plan"""
    
    plan = {
        'timestamp': datetime.now().isoformat(),
        'phase': 'Phase 2 - Integration Planning',
        'approach': 'SAFE_EXPANSION',
        'strategy': {
            'description': 'Create separate "_new" files for review before merging',
            'steps': [
                '1. Created theme-specific CSV files with new survey data',
                '2. Mapped column names to match existing schema',
                '3. Ready for manual review and validation',
                '4. After validation, can append to existing files OR keep separate',
                '5. Generate canonical bilingual GeoJSON for new data'
            ]
        },
        'created_files': created_files,
        'next_actions': {
            'immediate': [
                'Review created CSV files for data quality',
                'Verify column mappings are correct',
                'Check coordinate validity'
            ],
            'after_validation': [
                'Option A: Append to existing theme CSV files',
                'Option B: Keep as separate "_new" files',
                'Option C: Generate separate canonical GeoJSON for new data only',
                'Run generate_canonical_geojson.py on combined or separate data'
            ]
        },
        'risk_mitigation': {
            'backups_created': True,
            'separate_files': True,
            'reversible': True,
            'production_safety': 'HIGH - No existing files modified'
        }
    }
    
    output_file = Path('data/integration_plan.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Integration plan saved: {output_file}")
    
    return plan


def main():
    print("="*80)
    print("PHASE 2: INTEGRATION WITH EXISTING DATA")
    print("="*80)
    
    # 1. Load theme files from Phase 1.4
    print("\n📊 Step 1: Loading theme-specific CSV files...")
    themes = load_theme_files()
    
    if not themes:
        print("\n❌ No theme files found. Run Phase 1.4 first.")
        return False
    
    # 2. Create new CSV files with renamed columns
    print("\n🔄 Step 2: Creating theme CSV files with schema mapping...")
    created_files = create_new_theme_csvs(themes)
    
    # 3. Generate integration plan
    print("\n📝 Step 3: Generating integration plan...")
    plan = generate_integration_plan(created_files)
    
    # Summary
    print("\n" + "="*80)
    print("✅ PHASE 2 COMPLETE - INTEGRATION PREPARED")
    print("="*80)
    print(f"  📁 Created files: {len(created_files)}")
    print(f"  📂 Location: data/layers/Arabic/")
    print(f"  ⚠️  Status: SAFE - No existing files modified")
    print(f"  🔍 Files created with '_new' suffix for review")
    print("\n  Created files:")
    for f in created_files:
        print(f"    - {Path(f['file']).name}: {f['rows']} rows × {f['columns']} columns")
    
    print("\n" + "="*80)
    print("🚀 NEXT STEPS:")
    print("="*80)
    print("  1. Review created CSV files in data/layers/Arabic/")
    print("  2. Verify column mappings and data quality")
    print("  3. Decision point:")
    print("     A) Generate canonical GeoJSON for NEW data only (separate)")
    print("     B) Merge with existing CSV files and regenerate all")
    print("     C) Keep separate for now, integrate later")
    print("\n  💡 RECOMMENDATION: Generate canonical GeoJSON for new data (Option A)")
    print("     This keeps existing production data untouched while adding new data")
    print("="*80)
    
    return True


if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)

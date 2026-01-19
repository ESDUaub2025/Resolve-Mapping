"""
Phase 1.4: Column Mapping & Data Quality Validation
====================================================
Map 331 survey columns to 5 theme schemas and validate data quality

Process:
1. Load survey data with coordinates
2. Identify column structure (English/Arabic pairs)
3. Map to existing themes (Water, Energy, Food, General_Info, Regenerative_Agriculture)
4. Normalize column names (remove trailing colons, standardize spacing)
5. Handle checkbox arrays and multi-value fields
6. Validate data types and ranges
7. Export clean theme-specific CSV files
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Column mapping to themes
# Based on survey structure analysis and existing theme schemas
THEME_MAPPING = {
    'Water': [
        '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟',
        '11.في أي أشهر يتم زراعة هذين المحصولين؟',
        '12.ما هو نوع الري المستخدم لهذين المحصولين؟',
        '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟',
        '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟',
        '15.كم مرة تقوم بري هذين المحصولين في الأسبوع؟',
        '16.كيف تقيّم توفر المياه خلال موسم الزراعة؟',
        '17.هل تواجه نقصًا في المياه في أي وقت من السنة؟ إذا كانت الإجابة نعم، حدد الأشهر.',
    ],
    'Energy': [
        '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟',
        '18.ما هي كمية الطاقة (بالكيلووات أو اللترات من الوقود) التي تستخدمها خلال موسم الذروة؟',
    ],
    'Food': [
        '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟',
        '19.ما هو مستوى الإنتاج الحالي لكل من المحصولين (بالطن أو الوحدات)؟',
        '54.ما هي المنتجات الغذائية التقليدية التي تنتجها أو تشتري من المزارعين المحليين؟',
        '55.ما هي نسبة المشاركين في تحضير المؤونة في منطقتك؟',
        '63.هل لديك دواجن أو ماشية أخرى؟',
        '64.ما هي أنواع الحيوانات التي تربيها؟',
        '65.كم عدد الطيور التي تربيها؟',
        '66.ما نوع العلف الذي تستخدمه لتغذية الدواجن أو الماشية؟',
    ],
    'General_Info': [
        '4.القرية:',
        '5.هل تمتلك أرضاً زراعية؟',
        '6.أين تقع أرضك الزراعية؟',
        '7.كم عدد قطع الأرض الزراعية التي تملكها؟',
        '8.ما هو حجم الحيازة الزراعية الخاصة بك؟',
        '9.ما هو نوع التربة في أرضك؟',
        '20.هل لاحظت أي تغيرات في المناخ على مدى السنوات القليلة الماضية تؤثر على الزراعة؟',
        '21.ما هي التغيرات التي لاحظتها؟',
        '22.كيف أثرت هذه التغيرات على زراعتك؟',
        'X',
        'Y',
    ],
    'Regenerative_Agriculture': [
        '29.ما مدى معرفتك بمفهوم الزراعة التجديدية؟',
        '30.هل سمعت عن الزراعة التجديدية من قبل؟',
        '31.هل حضرت أي برامج تدريبية أو ورش عمل حول الزراعة التجديدية؟',
        '32.هل تمارس الزراعة التجديدية؟',
        '33.ما هي التقنيات التي تطبقها من الزراعة التجديدية؟',
        '38.ما هي أنواع المحسنات التي تستخدمها في التربة؟',
        '39.ما مدى اعتمادك على الأسمدة الكيميائية؟',
        '43.كيف تقوم بمكافحة الآفات؟',
        '44.ما مدى اعتمادك على المبيدات الكيميائية؟',
    ]
}

# Common fields across all themes
COMMON_FIELDS = [
    '1.اسم المُستجيب:',
    '4.القرية:',
    'X',
    'Y'
]


def load_survey_with_coords():
    """Load survey data with coordinates"""
    input_file = Path('data/MZSurvey farmers ENGLISH_with_coords.csv')
    
    if not input_file.exists():
        raise FileNotFoundError(f"Coordinate file not found: {input_file}")
    
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"✓ Loaded survey data: {len(df)} rows, {len(df.columns)} columns")
    
    return df


def normalize_column_name(col):
    """Normalize column name (remove trailing colons, extra spaces)"""
    if pd.isna(col):
        return col
    
    col = str(col).strip()
    
    # Remove trailing colon and space
    if col.endswith(':'):
        col = col[:-1].strip()
    
    # Normalize multiple spaces
    col = ' '.join(col.split())
    
    return col


def identify_column_pairs(df):
    """Identify English-Arabic column pairs"""
    columns = df.columns.tolist()
    pairs = []
    unpaired_en = []
    unpaired_ar = []
    
    i = 0
    while i < len(columns):
        col = columns[i]
        
        # Check if next column exists and might be a pair
        if i + 1 < len(columns):
            next_col = columns[i + 1]
            
            # Simple heuristic: if both start with same number (e.g., "4." and "4.")
            # or if one has Arabic and one doesn't
            col_has_arabic = any('\u0600' <= c <= '\u06FF' for c in str(col))
            next_has_arabic = any('\u0600' <= c <= '\u06FF' for c in str(next_col))
            
            if col_has_arabic != next_has_arabic:
                # Likely a pair
                if col_has_arabic:
                    pairs.append({'en': next_col, 'ar': col})
                else:
                    pairs.append({'en': col, 'ar': next_col})
                i += 2
                continue
        
        # Unpaired column
        if any('\u0600' <= c <= '\u06FF' for c in str(col)):
            unpaired_ar.append(col)
        else:
            unpaired_en.append(col)
        
        i += 1
    
    return pairs, unpaired_en, unpaired_ar


def map_columns_to_themes(df):
    """Map columns to themes based on content"""
    
    theme_columns = {
        'Water': [],
        'Energy': [],
        'Food': [],
        'General_Info': [],
        'Regenerative_Agriculture': []
    }
    
    unmapped_columns = []
    
    for col in df.columns:
        col_normalized = normalize_column_name(col)
        mapped = False
        
        # Check if column is in any theme mapping
        for theme, theme_cols in THEME_MAPPING.items():
            if col in theme_cols or col_normalized in theme_cols:
                theme_columns[theme].append(col)
                mapped = True
                break
        
        # Check common fields
        if not mapped and (col in COMMON_FIELDS or col_normalized in COMMON_FIELDS):
            for theme in theme_columns:
                if col not in theme_columns[theme]:
                    theme_columns[theme].append(col)
            mapped = True
        
        if not mapped:
            unmapped_columns.append(col)
    
    return theme_columns, unmapped_columns


def validate_data_quality(df):
    """Validate data quality and generate report"""
    
    issues = []
    warnings = []
    stats = {}
    
    # Check coordinates
    if 'X' in df.columns and 'Y' in df.columns:
        null_coords = df[df['X'].isna() | df['Y'].isna()]
        if len(null_coords) > 0:
            issues.append(f"Missing coordinates: {len(null_coords)} rows")
        
        # Check coordinate ranges (Lebanon bounds)
        if 'X' in df.columns:
            x_out_of_bounds = df[(df['X'] < 35.0) | (df['X'] > 37.0)]
            if len(x_out_of_bounds) > 0:
                warnings.append(f"Longitude out of bounds: {len(x_out_of_bounds)} rows")
        
        if 'Y' in df.columns:
            y_out_of_bounds = df[(df['Y'] < 33.0) | (df['Y'] > 35.0)]
            if len(y_out_of_bounds) > 0:
                warnings.append(f"Latitude out of bounds: {len(y_out_of_bounds)} rows")
        
        stats['coordinates'] = {
            'total_rows': len(df),
            'with_coords': int((df['X'].notna() & df['Y'].notna()).sum()),
            'missing_coords': int((df['X'].isna() | df['Y'].isna()).sum()),
            'lon_range': [float(df['X'].min()), float(df['X'].max())],
            'lat_range': [float(df['Y'].min()), float(df['Y'].max())]
        }
    
    # Check village names
    if '4.القرية:' in df.columns:
        village_col = '4.القرية:'
        villages = df[village_col].value_counts()
        stats['villages'] = {
            'unique_count': int(len(villages)),
            'distribution': {str(k): int(v) for k, v in villages.to_dict().items()}
        }
    
    # Check for duplicate rows
    duplicates = df.duplicated()
    if duplicates.sum() > 0:
        warnings.append(f"Duplicate rows found: {duplicates.sum()}")
    
    # Check data completeness by column type
    critical_cols = ['1.اسم المُستجيب:', '4.القرية:', 'X', 'Y']
    for col in critical_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                issues.append(f"Missing values in {col}: {null_count} rows")
    
    return issues, warnings, stats


def export_theme_csvs(df, theme_columns):
    """Export separate CSV files for each theme"""
    
    output_dir = Path('data/survey_by_theme')
    output_dir.mkdir(exist_ok=True)
    
    exported_files = []
    
    for theme, columns in theme_columns.items():
        if not columns:
            print(f"  ⚠️  {theme}: No columns mapped, skipping")
            continue
        
        # Select only mapped columns that exist in dataframe
        available_cols = [col for col in columns if col in df.columns]
        
        if not available_cols:
            print(f"  ⚠️  {theme}: No available columns in dataframe, skipping")
            continue
        
        theme_df = df[available_cols].copy()
        
        # Output files
        output_file = output_dir / f'MZSurvey_{theme}.csv'
        theme_df.to_csv(output_file, index=False, encoding='utf-8')
        
        exported_files.append({
            'theme': theme,
            'file': str(output_file),
            'rows': len(theme_df),
            'columns': len(theme_df.columns),
            'column_names': list(theme_df.columns)
        })
        
        print(f"  ✓ {theme}: {len(theme_df)} rows × {len(theme_df.columns)} columns → {output_file.name}")
    
    return exported_files


def generate_mapping_report(theme_columns, unmapped_columns, issues, warnings, stats, exported_files):
    """Generate comprehensive mapping report"""
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'phase': 'Phase 1.4 - Column Mapping & Data Quality',
        'summary': {
            'total_themes': len(theme_columns),
            'mapped_columns': sum(len(cols) for cols in theme_columns.values()),
            'unmapped_columns': len(unmapped_columns),
            'data_quality_issues': len(issues),
            'data_quality_warnings': len(warnings),
            'exported_files': len(exported_files)
        },
        'theme_mapping': {
            theme: {
                'column_count': len(cols),
                'columns': cols
            } for theme, cols in theme_columns.items()
        },
        'unmapped_columns': unmapped_columns,
        'data_quality': {
            'issues': issues,
            'warnings': warnings,
            'statistics': stats
        },
        'exported_files': exported_files
    }
    
    output_file = Path('data/column_mapping_report.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Mapping report saved: {output_file}")
    
    return report


def main():
    print("="*80)
    print("PHASE 1.4: COLUMN MAPPING & DATA QUALITY VALIDATION")
    print("="*80)
    
    # 1. Load data
    print("\n📊 Step 1: Loading survey data...")
    df = load_survey_with_coords()
    
    # 2. Map columns to themes
    print("\n🗺️  Step 2: Mapping columns to themes...")
    theme_columns, unmapped_columns = map_columns_to_themes(df)
    
    for theme, columns in theme_columns.items():
        print(f"  {theme}: {len(columns)} columns")
    
    if unmapped_columns:
        print(f"  ⚠️  Unmapped: {len(unmapped_columns)} columns")
    
    # 3. Validate data quality
    print("\n✅ Step 3: Validating data quality...")
    issues, warnings, stats = validate_data_quality(df)
    
    if issues:
        print("  ❌ Issues found:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✓ No critical issues")
    
    if warnings:
        print("  ⚠️  Warnings:")
        for warning in warnings:
            print(f"    - {warning}")
    
    # 4. Export theme-specific CSVs
    print("\n💾 Step 4: Exporting theme-specific CSV files...")
    exported_files = export_theme_csvs(df, theme_columns)
    
    # 5. Generate report
    print("\n📝 Step 5: Generating mapping report...")
    report = generate_mapping_report(theme_columns, unmapped_columns, issues, warnings, stats, exported_files)
    
    # Summary
    print("\n" + "="*80)
    print("✅ PHASE 1.4 COMPLETE")
    print("="*80)
    print(f"  📊 Themes mapped: {len(theme_columns)}")
    print(f"  📁 Files exported: {len(exported_files)}")
    print(f"  ✓ Data quality: {len(issues)} issues, {len(warnings)} warnings")
    
    if stats.get('coordinates'):
        coord_stats = stats['coordinates']
        print(f"  📍 Coordinates: {coord_stats['with_coords']}/{coord_stats['total_rows']} rows")
    
    if stats.get('villages'):
        village_stats = stats['villages']
        print(f"  🏘️  Villages: {village_stats['unique_count']} unique")
    
    print("="*80)
    
    if issues:
        print("\n❌ CRITICAL ISSUES DETECTED - REVIEW BEFORE PROCEEDING")
        return False
    else:
        print("\n🚀 READY FOR PHASE 2: Integration with Existing Data")
        return True


if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)

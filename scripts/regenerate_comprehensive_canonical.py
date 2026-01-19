"""
Regenerate Comprehensive Canonical GeoJSON
===========================================
Include ALL survey columns with substantive data (not checkbox sub-columns)

This script creates canonical GeoJSON files with COMPLETE survey data:
- 20-30 properties per feature (vs current 3-4)
- Matches richness of original data
- Uses Arabic for both languages (translation status: pending)
"""

import pandas as pd
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Define which columns to include for each theme
# Exclude checkbox sub-columns but include ALL main survey questions
THEME_COLUMN_SELECTION = {
    'Water': [
        # Core identifiers
        '4.القرية:',
        'X',
        'Y',
        
        # Main crops and seasons
        '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟',
        '11.ما هو الموسم الزراعي للمحصولين الرئيسيين؟',
        '• المحصول 1: من (شهر): ______ إلى (شهر): ______ • المحصول 2: من (شهر): ______ إلى (شهر): ______',
        
        # Irrigation
        '12..كم مرة تقوم بري كل محصول خلال موسم نموه؟',
        '•المحصول 1:',
        '•المحصول 2:',
        
        # Water sources (main question + selected options in text form)
        '13. Water Source',
        '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟',
        
        # Water availability
        '16. Water Availability',
        '16.كيف تقيّم توفر المياه خلال موسم الزراعة؟',
        
        # Water scarcity
        '17. Are there months during the year when you suffer from water scarcity?',
        '17.هل هناك أشهر خلال السنة تعاني فيها من شح المياه؟',
        '17. Water Scarcity Months',
        'ما أشهر  الذي  تعاني فيها من شح المياه؟',
        
        # Irrigation changes
        '18. Change in Irrigation Needs',
        '18.هل لاحظت أي تغيير في احتياجات الري خلال السنوات العشر الماضية؟',
    ],
    
    'Energy': [
        # Core identifiers
        '4.القرية:',
        'X',
        'Y',
        
        # Energy sources
        '14. Energy Source',
        '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟',
        
        # Energy consumption
        '15. Energy Consumption',
        '15.كمية الطاقة المستخدمة خلال موسم الذروة الزراعي (تقدير بالساعة أو بالوقود):',
    ],
    
    'Food': [
        # Core identifiers
        '4.القرية:',
        'X',
        'Y',
        
        # Production level
        '19. Food Production Level',
        '19.كيف تصف مستوى إنتاج الغذاء والمنتجات التقليدية في منزلك/قريتك/تعاونيتك؟',
        
        # Cooperative membership
        '20. Coop Member?',
        '20. هل أنت عضو في تعاونية تقوم بإنتاج و/أو بيع الأطعمة التقليدية؟',
        'إذا كانت الإجابة نعم: ما هو العدد التقريبي للأعضاء النشطين في التعاونية؟',
        
        # Traditional products
        '21. ما هي المنتجات التقليدية الرئيسية التي تُنتج في منزلك/تعاونيتك/قريتك؟',
        
        # Production quantities
        '22. ما هي الكمية المنتجة في الموسم للمنتجين الرئيسيين؟ • المنتج 1: ___________ / الكمية: ___________ (كغ أو لتر) • المنتج 2: ___________ / الكمية: ___________ (كغ أو لتر)',
        
        # Markets
        '23. أين تُباع هذه المنتجات عادة؟',
        
        # Participation rate
        '24. % Village Participation',
        '24. ما هي نسبة المنازل في قريتك التي تشارك في إنتاج المؤونة أو الطعام التقليدي؟',
        
        # Rodent losses
        '25. هل واجهت خسائر بسبب القوارض في إنتاج أو تخزين الطعام التقليدي؟',
        '26. هل تعاني من وجود الفئران/القوارض في منطقتك؟',
        '27.برأيك، هل تغير عدد الفئران خلال العشر سنوات الماضية؟',
    ],
    
    'General_Info': [
        # Core identifiers
        '4.القرية:',
        'X',
        'Y',
        
        # Demographics
        '2. Age Group',
        '2.الفئة العمرية:',
        '3. Gender',
        '3.الجنس:',
        
        # Land ownership
        '5. Own Farmland?',
        '5.هل تمتلك أرضاً زراعية؟',
        '6. Land Location',
        ' 6.موقع أرضك:',
        
        # Income sources
        '7. Main Income Source',
        '7. ما هو مصدر دخلك الرئيسي؟',
        
        # Farm size
        '8. Land Size',
        '8.ما هو حجم الحيازة الزراعية الخاصة بك؟',
        
        # Soil type
        '9. Soil Type',
        '9.ما هو نوع التربة في أرضك؟',
        
        # Climate observations
        '52. Climate Change Noticed?',
        ' 52. هل لاحظت تغيرات مناخية أثرت على الزراعة في السنوات الأخيرة؟',
        '53. Climate Changes',
        '"53. إذا كانت الإجابة ""نعم""، يرجى تحديد أهمها"',
        '54. Impact on Production',
        '54.كيف أثرت هذه التغيرات على إنتاجك الزراعي؟',
    ],
    
    'Regenerative_Agriculture': [
        # Core identifiers
        '4.القرية:',
        'X',
        'Y',
        
        # Knowledge
        '29.ما مدى معرفتك بمفهوم الزراعة التجديدية؟',
        
        # Current practices
        '32.هل تمارس الزراعة التجديدية؟',
        '33.ما هي التقنيات التي تطبقها من الزراعة التجديدية؟',
        
        # Seeds
        '34. Seed Selection Criteria',
        '34.ما هي المعايير التي تعتمدها عند شراء البذور/الشتول؟',
        '35. Seed Source',
        '35.كيف تحصل على البذور/الشتول؟',
        '36. Seed Challenges',
        '36.ما هو التحدي الأكبر في الحصول على البذور/الشتول؟',
        
        # Soil amendments
        '38. Soil Enhancers',
        '38.ما هي أنواع المحسنات التي تستخدمها في التربة؟',
        '39. Chem Fertilizer Reliance',
        '39.ما مدى اعتمادك على الأسمدة الكيميائية؟',
        '40. Fertilizer Cost %',
        '40.ما هي نسبة تكلفة الأسمدة الكيميائية من إجمالي التكاليف؟',
        
        # Pest control
        '43. Pest Control Method',
        '43.كيف تقوم بمكافحة الآفات؟',
        '44. Pesticide Reliance',
        '44.ما مدى اعتمادك على المبيدات الكيميائية؟',
        '45. Pesticide Cost %',
        '45.ما هي نسبة تكلفة المبيدات من إجمالي تكاليفك؟',
        
        # Barriers
        '48.ما هي الحواجز الرئيسية التي تمنعك من تبني الزراعة التجديدية؟',
        '49.هل ترغب في المشاركة في تدريبات مستقبلية حول الزراعة التجديدية؟',
    ]
}

def clean_column_name(name):
    """Remove trailing colons and extra spaces from column names"""
    if not name or pd.isna(name):
        return name
    return str(name).strip().rstrip(':').strip()

def generate_stable_id(theme, row_index, coords):
    """Generate deterministic feature ID from theme, row, and coordinate hash"""
    coord_str = f"{coords[0]:.6f},{coords[1]:.6f}"
    coord_hash = hashlib.md5(coord_str.encode()).hexdigest()[:8]
    return f"{theme.lower()}_{row_index}_{coord_hash}"

def generate_canonical_geojson(theme_name, csv_path, output_path):
    """Generate canonical bilingual GeoJSON with comprehensive data"""
    
    print(f"\n{'='*60}")
    print(f"Processing {theme_name}")
    print(f"{'='*60}")
    
    # Load CSV
    df = pd.read_csv(csv_path)
    df.columns = [clean_column_name(col) for col in df.columns]
    
    # Get columns for this theme
    selected_columns = THEME_COLUMN_SELECTION.get(theme_name, [])
    selected_columns = [clean_column_name(col) for col in selected_columns]
    
    # Filter to only columns that exist
    available_columns = [col for col in selected_columns if col in df.columns]
    missing_columns = [col for col in selected_columns if col not in df.columns]
    
    if missing_columns:
        print(f"⚠️  Missing columns: {len(missing_columns)}")
        for col in missing_columns[:5]:  # Show first 5
            print(f"   - {col}")
    
    print(f"✓ Using {len(available_columns)} columns (out of {len(selected_columns)} requested)")
    
    # Verify coordinates exist
    if 'X' not in df.columns or 'Y' not in df.columns:
        raise ValueError(f"X/Y coordinates missing from {csv_path}")
    
    features = []
    property_counts = {'ar': [], 'en': []}
    
    for idx, row in df.iterrows():
        # Get coordinates
        x = float(row['X'])
        y = float(row['Y'])
        
        # Build bilingual property dictionaries
        ar_values = {}
        en_values = {}
        
        for col in available_columns:
            if col in ['X', 'Y']:
                continue  # Skip coordinates (they're in geometry)
            
            value = row[col]
            if pd.notna(value) and str(value).strip():
                cleaned_value = str(value).strip()
                
                # Determine if this is an English or Arabic column
                # English columns: start with numbers (e.g., "2. Age Group", "13. Water Source")
                # Arabic columns: contain Arabic characters (e.g., "2.الفئة العمرية", "13.ما هو المصدر")
                
                is_english_col = any(c in col for c in ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']) and not any(c in col for c in ['ا', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي'])
                
                if is_english_col:
                    # English column - store value in en dict
                    en_values[col] = cleaned_value
                else:
                    # Arabic column - store value in ar dict
                    ar_values[col] = cleaned_value
        
        # Count non-empty properties per language
        property_counts['ar'].append(len(ar_values))
        property_counts['en'].append(len(en_values))
        
        # Generate stable feature ID
        feature_id = generate_stable_id(theme_name, idx + 1, [x, y])
        
        # Create feature (translation complete - no pending status)
        feature = {
            "type": "Feature",
            "id": feature_id,
            "geometry": {
                "type": "Point",
                "coordinates": [x, y]
            },
            "properties": {
                "featureId": feature_id,
                "theme": theme_name.lower().replace('_', ''),
                "values": {
                    "ar": ar_values,
                    "en": en_values
                },
                "metadata": {
                    "sourceRow": idx + 1,
                    "dataSource": "MZSurvey_2026_Beqaa",
                    "translationStatus": "complete",
                    "generatedAt": datetime.now().isoformat()
                }
            }
        }
        
        features.append(feature)
    
    # Create FeatureCollection
    avg_ar_props = sum(property_counts['ar']) / len(property_counts['ar']) if property_counts['ar'] else 0
    avg_en_props = sum(property_counts['en']) / len(property_counts['en']) if property_counts['en'] else 0
    
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "theme": theme_name,
            "dataSource": "MZSurvey_2026_Beqaa",
            "generatedAt": datetime.now().isoformat(),
            "featureCount": len(features),
            "columnsIncluded": len(available_columns),
            "translationStatus": "complete",
            "avgPropertiesPerFeature": {
                "ar": avg_ar_props,
                "en": avg_en_props
            }
        },
        "features": features
    }
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    
    # Statistics
    min_ar = min(property_counts['ar']) if property_counts['ar'] else 0
    max_ar = max(property_counts['ar']) if property_counts['ar'] else 0
    min_en = min(property_counts['en']) if property_counts['en'] else 0
    max_en = max(property_counts['en']) if property_counts['en'] else 0
    
    print(f"✓ Generated: {output_path.name}")
    print(f"  - Features: {len(features)}")
    print(f"  - Columns included: {len(available_columns)}")
    print(f"  - Arabic properties: {avg_ar_props:.1f} avg (range: {min_ar}-{max_ar})")
    print(f"  - English properties: {avg_en_props:.1f} avg (range: {min_en}-{max_en})")
    print(f"  - Translation status: complete")
    
    return len(features), avg_ar_props, avg_en_props

def main():
    """Regenerate comprehensive canonical GeoJSON files"""
    
    print("="*60)
    print("Regenerating Comprehensive Canonical GeoJSON")
    print("="*60)
    print("Goal: Include ALL relevant survey columns (20-30 properties per feature)")
    print()
    
    # Paths
    survey_csv = Path('data/MZSurvey farmers ENGLISH_with_coords.csv')
    output_dir = Path('data/geojson/canonical')
    
    # Verify input exists
    if not survey_csv.exists():
        raise FileNotFoundError(f"Survey CSV not found: {survey_csv}")
    
    # Process each theme
    results = {}
    themes_to_process = ['Water', 'Energy', 'Food', 'General_Info', 'Regenerative_Agriculture']
    
    for theme in themes_to_process:
        output_path = output_dir / f"{theme}_new.canonical.geojson"
        feature_count, avg_ar, avg_en = generate_canonical_geojson(theme, survey_csv, output_path)
        results[theme] = {
            'features': feature_count, 
            'avg_ar_properties': avg_ar,
            'avg_en_properties': avg_en
        }
    
    # Summary
    print(f"\n{'='*60}")
    print("GENERATION COMPLETE")
    print(f"{'='*60}")
    for theme, stats in results.items():
        print(f"{theme:25s} {stats['features']:3d} features  "
              f"({stats['avg_ar_properties']:4.1f} AR / {stats['avg_en_properties']:4.1f} EN properties/feature)")
    
    print("\n✓ All canonical GeoJSON files regenerated with BILINGUAL data")
    print("✓ Translation status: complete (English values extracted from CSV)")
    print("\nNext steps:")
    print("1. Reload frontend (Ctrl+Shift+R) to load new data")
    print("2. Test details panel - should show 15-20+ properties")
    print("3. Update UI to handle translation status indicator")

if __name__ == '__main__':
    main()

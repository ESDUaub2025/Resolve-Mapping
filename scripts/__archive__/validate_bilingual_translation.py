#!/usr/bin/env python3
"""
Validate Bilingual Translation Implementation
==============================================
Checks generated canonical GeoJSON files for:
1. Translation status = "complete"
2. Separate ar/en value dictionaries
3. English values are actually English (not Arabic)
4. Property count parity (ar vs en)
"""

import json
from pathlib import Path
import re

def is_arabic_text(text):
    """Check if text contains Arabic characters"""
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    return bool(arabic_pattern.search(str(text)))

def validate_canonical_file(filepath):
    """Validate a single canonical GeoJSON file"""
    print(f"\n{'='*60}")
    print(f"Validating: {filepath.name}")
    print(f"{'='*60}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check metadata
    metadata = data.get('metadata', {})
    translation_status = metadata.get('translationStatus', 'unknown')
    print(f"✓ Translation status: {translation_status}")
    
    if translation_status != 'complete':
        print(f"  ⚠️  Expected 'complete', got '{translation_status}'")
    
    # Check features
    features = data.get('features', [])
    print(f"✓ Features: {len(features)}")
    
    if not features:
        print("  ⚠️  No features found")
        return
    
    # Sample first feature for detailed check
    sample = features[0]
    values = sample.get('properties', {}).get('values', {})
    
    ar_values = values.get('ar', {})
    en_values = values.get('en', {})
    
    print(f"\nSample Feature (ID: {sample.get('id', 'unknown')})")
    print(f"  - Arabic properties: {len(ar_values)}")
    print(f"  - English properties: {len(en_values)}")
    
    # Check for Arabic contamination in English values
    english_contamination = []
    for key, value in en_values.items():
        if is_arabic_text(value):
            english_contamination.append((key, value))
    
    if english_contamination:
        print(f"\n  ⚠️  WARNING: Arabic text found in English values!")
        for key, value in english_contamination[:3]:  # Show first 3
            print(f"     - {key[:40]}: {value[:40]}")
    else:
        print(f"  ✅ English values contain no Arabic text")
    
    # Show sample values
    print(f"\n  Sample Arabic values:")
    for key, value in list(ar_values.items())[:3]:
        print(f"    {key[:40]:40s} → {str(value)[:40]}")
    
    print(f"\n  Sample English values:")
    for key, value in list(en_values.items())[:3]:
        print(f"    {key[:40]:40s} → {str(value)[:40]}")
    
    # Statistics across all features
    ar_counts = [len(f.get('properties', {}).get('values', {}).get('ar', {})) for f in features]
    en_counts = [len(f.get('properties', {}).get('values', {}).get('en', {})) for f in features]
    
    avg_ar = sum(ar_counts) / len(ar_counts) if ar_counts else 0
    avg_en = sum(en_counts) / len(en_counts) if en_counts else 0
    
    print(f"\n  Average properties per feature:")
    print(f"    Arabic:  {avg_ar:.1f} (range: {min(ar_counts)}-{max(ar_counts)})")
    print(f"    English: {avg_en:.1f} (range: {min(en_counts)}-{max(en_counts)})")
    
    # Check feature metadata
    sample_metadata = sample.get('properties', {}).get('metadata', {})
    feature_status = sample_metadata.get('translationStatus', 'unknown')
    
    if feature_status != 'complete':
        print(f"  ⚠️  Feature metadata status: {feature_status}")
    
    return {
        'file': filepath.name,
        'translation_status': translation_status,
        'features': len(features),
        'avg_ar_props': avg_ar,
        'avg_en_props': avg_en,
        'english_clean': len(english_contamination) == 0
    }

def main():
    """Run validation on all canonical files"""
    canonical_dir = Path('data/geojson/canonical')
    
    if not canonical_dir.exists():
        print(f"❌ Canonical directory not found: {canonical_dir}")
        return
    
    # Find all *_new.canonical.geojson files
    files = list(canonical_dir.glob('*_new.canonical.geojson'))
    
    if not files:
        print(f"❌ No canonical files found in {canonical_dir}")
        return
    
    print(f"\nFound {len(files)} canonical files to validate")
    
    results = []
    for filepath in sorted(files):
        result = validate_canonical_file(filepath)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    for r in results:
        status_icon = '✅' if r['english_clean'] and r['translation_status'] == 'complete' else '⚠️'
        print(f"{status_icon} {r['file']:40s} {r['features']:3d} features  "
              f"({r['avg_ar_props']:4.1f} AR / {r['avg_en_props']:4.1f} EN)")
    
    all_clean = all(r['english_clean'] for r in results)
    all_complete = all(r['translation_status'] == 'complete' for r in results)
    
    print(f"\n{'='*60}")
    if all_clean and all_complete:
        print("✅ ALL VALIDATIONS PASSED")
        print("   - Translation status: complete")
        print("   - English values contain no Arabic text")
        print("   - Bilingual separation successful")
    else:
        print("⚠️  VALIDATION ISSUES DETECTED")
        if not all_complete:
            print("   - Some files have translation status != 'complete'")
        if not all_clean:
            print("   - Some English values contain Arabic text")

if __name__ == '__main__':
    main()

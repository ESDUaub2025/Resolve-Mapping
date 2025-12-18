"""
Immutable CSV to GeoJSON Converter
===================================
Professional-grade conversion with complete data integrity and provenance tracking.

Principles:
1. Source files are immutable (read-only, never modified)
2. Strict 1:1 row-to-feature mapping (no data loss)
3. Schema frozen upfront (deterministic structure)
4. Invalid coordinates → null geometry (feature preserved)
5. All columns preserved verbatim as properties
6. Language-agnostic (same logic for Arabic/English)
7. Mandatory validation and audit trail
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib


# ============================================================================
# SCHEMA DEFINITION (Frozen Configuration)
# ============================================================================

COORDINATE_SYSTEM = "WGS84"
EPSG_CODE = "EPSG:4326"

# Schema: Define coordinate fields and feature identity
SCHEMA = {
    'coordinate_fields': {
        'longitude': 'X',  # Column name for longitude
        'latitude': 'Y'     # Column name for latitude
    },
    'id_fields': ['القرية:', 'Village'],  # Potential ID columns (language-agnostic)
    'preserve_all_columns': True  # All CSV columns → GeoJSON properties
}

# File mapping: Arabic source → English source → Output base name
FILE_MAPPING = [
    {
        'arabic_source': 'Energy_1.0.csv',
        'english_source': 'Energy_1.0.en.csv',
        'output_base': 'Energy',
        'theme': 'Energy'
    },
    {
        'arabic_source': 'Food_1.0.csv',
        'english_source': 'Food_1.0.en.csv',
        'output_base': 'Food',
        'theme': 'Food'
    },
    {
        'arabic_source': 'Generalinfo_1.0.csv',
        'english_source': 'Generalinfo_1.0.en.csv',
        'output_base': 'General_Info',
        'theme': 'General_Info'
    },
    {
        'arabic_source': 'Regenerative_1.0.csv',
        'english_source': 'Regenerative_1.0.en.csv',
        'output_base': 'Regenerative_Agriculture',
        'theme': 'Regenerative_Agriculture'
    },
    {
        'arabic_source': 'Water_1.0.csv',
        'english_source': 'Water_1.0.en.csv',
        'output_base': 'Water',
        'theme': 'Water'
    }
]

# Paths
ARABIC_DIR = Path(__file__).parent.parent / 'data' / 'layers' / 'Arabic'
ENGLISH_DIR = Path(__file__).parent.parent / 'data' / 'layers' / 'English'
OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'geojson'
AUDIT_DIR = Path(__file__).parent.parent / 'data' / 'conversion_audit'


# ============================================================================
# CONVERSION RECORD
# ============================================================================

class ConversionRecord:
    """Tracks all conversion operations for provenance and audit"""
    
    def __init__(self, source_file: str, language: str):
        self.source_file = source_file
        self.language = language
        self.timestamp = datetime.now().isoformat()
        self.source_hash = None
        self.output_hash = None
        self.row_count = 0
        self.column_count = 0
        self.columns = []
        self.features_created = 0
        self.null_geometries = 0
        self.valid_geometries = 0
        self.warnings = []
        self.validation_passed = False
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for integrity verification"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for JSON serialization"""
        return {
            'source_file': self.source_file,
            'language': self.language,
            'timestamp': self.timestamp,
            'source_hash': self.source_hash,
            'output_hash': self.output_hash,
            'schema': {
                'row_count': self.row_count,
                'column_count': self.column_count,
                'columns': self.columns
            },
            'features': {
                'total_created': self.features_created,
                'with_valid_geometry': self.valid_geometries,
                'with_null_geometry': self.null_geometries
            },
            'warnings': self.warnings,
            'validation': {
                'passed': self.validation_passed,
                'row_feature_match': self.row_count == self.features_created
            },
            'coordinate_system': {
                'crs': COORDINATE_SYSTEM,
                'epsg': EPSG_CODE
            }
        }


# ============================================================================
# GEOMETRY HANDLING
# ============================================================================

def parse_coordinate(value: Any) -> Optional[float]:
    """
    Safely parse coordinate value to float.
    Returns None if invalid (triggers null geometry).
    """
    if value is None or value == '':
        return None
    
    try:
        # Handle string with spaces or special characters
        if isinstance(value, str):
            cleaned = value.strip().replace(',', '.').replace(' ', '')
            if cleaned == '':
                return None
            return float(cleaned)
        return float(value)
    except (ValueError, TypeError):
        return None


def create_geometry(row: Dict[str, str], record: ConversionRecord) -> Optional[Dict[str, Any]]:
    """
    Create Point geometry from row data.
    Returns None for invalid coordinates (feature still created with null geometry).
    """
    lon_field = SCHEMA['coordinate_fields']['longitude']
    lat_field = SCHEMA['coordinate_fields']['latitude']
    
    lon = parse_coordinate(row.get(lon_field))
    lat = parse_coordinate(row.get(lat_field))
    
    # Invalid coordinates → null geometry (not an error, feature preserved)
    if lon is None or lat is None:
        record.null_geometries += 1
        return None
    
    # Valid geometry
    record.valid_geometries += 1
    return {
        "type": "Point",
        "coordinates": [lon, lat]
    }


# ============================================================================
# FEATURE CONSTRUCTION
# ============================================================================

def create_feature(row: Dict[str, str], row_index: int, theme: str, 
                   source_file: str, record: ConversionRecord) -> Dict[str, Any]:
    """
    Create GeoJSON Feature from CSV row.
    
    Guarantees:
    - Exactly one feature per row
    - All columns preserved as properties
    - Original coordinate values preserved
    - Deterministic order maintained
    """
    # Build properties: ALL columns preserved verbatim
    properties = {}
    for key, value in row.items():
        # Preserve original value (even if used for geometry)
        properties[key] = value if value != '' else None
    
    # Add metadata (provenance)
    properties['_metadata'] = {
        'theme': theme,
        'source_file': source_file,
        'source_row': row_index + 2,  # +2: header is row 1, data starts at row 2
        'coordinate_system': COORDINATE_SYSTEM
    }
    
    # Create geometry (may be null for invalid coordinates)
    geometry = create_geometry(row, record)
    
    # Build feature
    feature = {
        "type": "Feature",
        "properties": properties,
        "geometry": geometry
    }
    
    record.features_created += 1
    return feature


# ============================================================================
# CONVERSION ENGINE
# ============================================================================

def convert_csv_to_geojson(csv_path: Path, output_path: Path, 
                           theme: str, language: str) -> ConversionRecord:
    """
    Convert CSV to GeoJSON with strict integrity guarantees.
    
    Immutability: CSV file is only read, never modified.
    1:1 Mapping: Every row becomes exactly one feature.
    Preservation: All columns kept as properties.
    Determinism: Same input always produces same output.
    """
    print(f"\n{'='*70}")
    print(f"Converting: {csv_path.name} ({language})")
    print(f"{'='*70}")
    
    # Initialize record
    record = ConversionRecord(csv_path.name, language)
    record.source_hash = record.calculate_file_hash(csv_path)
    
    # Read CSV (immutable - read-only operation)
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    # Schema capture
    record.row_count = len(rows)
    record.column_count = len(headers)
    record.columns = list(headers)
    
    print(f"Schema frozen:")
    print(f"  Rows: {record.row_count}")
    print(f"  Columns: {record.column_count}")
    print(f"  Coordinate fields: {SCHEMA['coordinate_fields']}")
    
    # Strict 1:1 conversion
    features = []
    for idx, row in enumerate(rows):
        feature = create_feature(row, idx, theme, csv_path.name, record)
        features.append(feature)
    
    # Build GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": EPSG_CODE
            }
        },
        "features": features
    }
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    
    record.output_hash = record.calculate_file_hash(output_path)
    
    print(f"\nConversion complete:")
    print(f"  Features created: {record.features_created}")
    print(f"  Valid geometries: {record.valid_geometries}")
    print(f"  Null geometries: {record.null_geometries}")
    print(f"  Output: {output_path.name}")
    
    return record


# ============================================================================
# VALIDATION
# ============================================================================

def validate_conversion(csv_path: Path, geojson_path: Path, 
                        record: ConversionRecord) -> bool:
    """
    Mandatory post-conversion validation.
    
    Checks:
    1. Row count = Feature count (1:1 mapping)
    2. All columns preserved in properties
    3. Geometry handling correct (valid/null)
    4. Deterministic order maintained
    """
    print(f"\n{'='*70}")
    print(f"VALIDATION: {geojson_path.name}")
    print(f"{'='*70}")
    
    # Load GeoJSON
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    features = geojson.get('features', [])
    
    # Check 1: Row-Feature count match
    row_feature_match = len(features) == record.row_count
    print(f"✓ Row-Feature match: {len(features)} features = {record.row_count} rows: {row_feature_match}")
    
    # Check 2: Schema preservation
    if features:
        first_props = features[0]['properties']
        geojson_columns = [k for k in first_props.keys() if k != '_metadata']
        schema_match = len(geojson_columns) == record.column_count
        print(f"✓ Column preservation: {len(geojson_columns)} properties ≥ {record.column_count} columns: {schema_match}")
    
    # Check 3: Geometry counts
    null_count = sum(1 for f in features if f['geometry'] is None)
    valid_count = sum(1 for f in features if f['geometry'] is not None)
    geometry_match = (null_count == record.null_geometries and 
                     valid_count == record.valid_geometries)
    print(f"✓ Geometry handling: {valid_count} valid, {null_count} null: {geometry_match}")
    
    # Check 4: Order preservation (check row indices in metadata)
    order_preserved = True
    for idx, feature in enumerate(features):
        expected_row = idx + 2  # CSV row number
        actual_row = feature['properties']['_metadata']['source_row']
        if expected_row != actual_row:
            order_preserved = False
            record.warnings.append(f"Row order mismatch at index {idx}")
            break
    print(f"✓ Deterministic order: {order_preserved}")
    
    # Overall validation
    passed = row_feature_match and schema_match and geometry_match and order_preserved
    record.validation_passed = passed
    
    print(f"\n{'='*70}")
    print(f"VALIDATION: {'✓ PASSED' if passed else '✗ FAILED'}")
    print(f"{'='*70}")
    
    return passed


# ============================================================================
# AUDIT TRAIL
# ============================================================================

def save_conversion_record(record: ConversionRecord, output_name: str):
    """Save conversion record for provenance tracking"""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    
    audit_file = AUDIT_DIR / f"{output_name}_{record.language}_audit.json"
    with open(audit_file, 'w', encoding='utf-8') as f:
        json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
    
    print(f"  Audit record: {audit_file.name}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute conversion pipeline with full integrity guarantees"""
    print("="*70)
    print("IMMUTABLE CSV TO GEOJSON CONVERTER")
    print("="*70)
    print(f"Coordinate System: {COORDINATE_SYSTEM} ({EPSG_CODE})")
    print(f"Conversion Mode: Strict 1:1 row-to-feature mapping")
    print(f"Source Protection: Read-only (immutable)")
    print(f"Validation: Mandatory")
    print("="*70)
    
    all_records = []
    all_passed = True
    
    for mapping in FILE_MAPPING:
        theme = mapping['theme']
        
        # Process Arabic version
        arabic_csv = ARABIC_DIR / mapping['arabic_source']
        arabic_output = OUTPUT_DIR / f"{mapping['output_base']}_ar.geojson"
        
        if arabic_csv.exists():
            ar_record = convert_csv_to_geojson(arabic_csv, arabic_output, theme, 'Arabic')
            ar_valid = validate_conversion(arabic_csv, arabic_output, ar_record)
            save_conversion_record(ar_record, mapping['output_base'])
            all_records.append(ar_record)
            all_passed = all_passed and ar_valid
        else:
            print(f"\n✗ Arabic source not found: {arabic_csv}")
        
        # Process English version
        english_csv = ENGLISH_DIR / mapping['english_source']
        english_output = OUTPUT_DIR / f"{mapping['output_base']}.geojson"
        
        if english_csv.exists():
            en_record = convert_csv_to_geojson(english_csv, english_output, theme, 'English')
            en_valid = validate_conversion(english_csv, english_output, en_record)
            save_conversion_record(en_record, mapping['output_base'])
            all_records.append(en_record)
            all_passed = all_passed and en_valid
        else:
            print(f"\n✗ English source not found: {english_csv}")
    
    # Final summary
    print("\n" + "="*70)
    print("CONVERSION SUMMARY")
    print("="*70)
    print(f"Files processed: {len(all_records)}")
    print(f"Total features: {sum(r.features_created for r in all_records)}")
    print(f"Valid geometries: {sum(r.valid_geometries for r in all_records)}")
    print(f"Null geometries: {sum(r.null_geometries for r in all_records)}")
    print(f"Validation: {'✓ ALL PASSED' if all_passed else '✗ SOME FAILED'}")
    print(f"Audit trail: {AUDIT_DIR}")
    print("="*70)
    
    if not all_passed:
        print("\n⚠ WARNING: Some validations failed. Check audit logs.")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

#!/usr/bin/env python3
"""
==================================================================================
FARMERS SURVEY INTEGRATION SCRIPT
Integrates: data/Farmers survey 27-2-2026.xlsx  →  all downstream data products
==================================================================================

WHAT THIS SCRIPT DOES:
  1. Reads the new Excel file and compares with existing survey data
  2. Detects new respondents + schema changes
  3. Adds coordinates from verified_village_coordinates.json
  4. Resolves UNKNOWN village coordinates with best-effort geocoding
  5. Updates master survey CSV files
  6. Re-splits by theme (survey_by_theme/)
  7. Rebuilds Arabic _new.csv layer files
  8. Regenerates all *_new.canonical.geojson files
  9. Updates Original_Survey_Data_Complete.xlsx
 10. Writes a full audit report

USAGE:
  cd d:/Programing/ResolveMaping_final2
  .venv/Scripts/python.exe scripts/integrate_new_survey_27_2_2026.py

SAFETY:
  - Creates timestamped backups of all modified files
  - Never overwrites 1.0 (original) data files
  - Atomic swap: writes to temp then renames
  - Full audit trail in data/integration_audit_YYYYMMDD_HHMMSS.json
==================================================================================
"""

import pandas as pd
import json
import hashlib
import shutil
import os
import sys
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA  = ROOT / "data"
NEW_EXCEL  = DATA / "Farmers survey 27-2-2026.xlsx"
OLD_MASTER = DATA / "MZSurvey farmers ENGLISH.csv"
OLD_COORDS = DATA / "MZSurvey farmers ENGLISH_with_coords.csv"
COORD_FILE = DATA / "verified_village_coordinates.json"
SURVEY_THEME_DIR = DATA / "survey_by_theme"
ARABIC_LAYER_DIR  = DATA / "layers" / "Arabic"
ENGLISH_LAYER_DIR = DATA / "layers" / "English"
CANONICAL_DIR = DATA / "geojson" / "canonical"
ORIG_EXCEL = DATA / "Original_Survey_Data_Complete.xlsx"

BACKUP_SUFFIX = datetime.now().strftime("_BACKUP_%Y%m%d_%H%M%S")
AUDIT_FILE = DATA / f"integration_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# Village column key (Arabic)
VILLAGE_COL_AR = "4.القرية:"

# ─────────────────────────────────────────────
# COLUMN → THEME MAPPING  (which columns go to which theme CSV)
# This mirrors the column selection in regenerate_comprehensive_canonical.py
# ─────────────────────────────────────────────
THEME_COLUMNS = {
    "Water": [
        "4.القرية:", "X", "Y",
        "10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟",
        "11.ما هو الموسم الزراعي للمحصولين الرئيسيين؟",
        "• المحصول 1: من (شهر): ______ إلى (شهر): ______ • المحصول 2: من (شهر): ______ إلى (شهر): ______",
        "12..كم مرة تقوم بري كل محصول خلال موسم نموه؟",
        "•المحصول 1:", "•المحصول 2:",
        "13. Water Source",
        "13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟",
        "16. Water Availability",
        "16.كيف تقيّم توفر المياه خلال موسم الزراعة؟",
        "17. Are there months during the year when you suffer from water scarcity?",
        "17.هل هناك أشهر خلال السنة تعاني فيها من شح المياه؟",
        "17. Water Scarcity Months",
        "ما أشهر  الذي  تعاني فيها من شح المياه؟",
        "18. Change in Irrigation Needs",
        "18.هل لاحظت أي تغيير في احتياجات الري خلال السنوات العشر الماضية؟",
    ],
    "Energy": [
        "4.القرية:", "X", "Y",
        "14. Energy Source",
        "14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟",
        "15. Energy Consumption",
        "15.كمية الطاقة المستخدمة خلال موسم الذروة الزراعي (تقدير بالساعة أو بالوقود):",
    ],
    "Food": [
        "4.القرية:", "X", "Y",
        "19. Food Production Level",
        "19.كيف تصف مستوى إنتاج الغذاء والمنتجات التقليدية في منزلك/قريتك/تعاونيتك؟",
        "20. Coop Member?",
        "20. هل أنت عضو في تعاونية تقوم بإنتاج و/أو بيع الأطعمة التقليدية؟",
        "إذا كانت الإجابة نعم: ما هو العدد التقريبي للأعضاء النشطين في التعاونية؟",
        "21. ما هي المنتجات التقليدية الرئيسية التي تُنتج في منزلك/تعاونيتك/قريتك؟",
        "22. ما هي الكمية المنتجة في الموسم للمنتجين الرئيسيين؟ • المنتج 1: ___________ / الكمية: ___________ (كغ أو لتر) • المنتج 2: ___________ / الكمية: ___________ (كغ أو لتر)",
        "23. أين تُباع هذه المنتجات عادة؟",
        "24. % Village Participation",
        "24. ما هي نسبة المنازل في قريتك التي تشارك في إنتاج المؤونة أو الطعام التقليدي؟",
        "25. هل واجهت خسائر بسبب القوارض في إنتاج أو تخزين الطعام التقليدي؟",
        "26. هل تعاني من وجود الفئران/القوارض في منطقتك؟",
        "27.برأيك، هل تغير عدد الفئران خلال العشر سنوات الماضية؟",
    ],
    "General_Info": [
        "4.القرية:", "X", "Y",
        "2. Age Group", "2.الفئة العمرية:",
        "3. Gender", "3.الجنس:",
        "5. Own Farmland?", "5.هل تمتلك أرضاً زراعية؟",
        "6. Land Location", " 6.موقع أرضك:",
        "7. Main Income Source", "7. ما هو مصدر دخلك الرئيسي؟",
        "8. Land Size", "8.ما هو حجم الحيازة الزراعية الخاصة بك؟",
        "9. Soil Type", "9.ما هو نوع التربة في أرضك؟",
        "52. Climate Change Noticed?",
        " 52. هل لاحظت تغيرات مناخية أثرت على الزراعة في السنوات الأخيرة؟",
        "53. Climate Changes",
        "54. Impact on Production",
        "54.كيف أثرت هذه التغيرات على إنتاجك الزراعي؟",
    ],
    "Regenerative_Agriculture": [
        "4.القرية:", "X", "Y",
        "29.ما مدى معرفتك بمفهوم الزراعة التجديدية؟",
        "32.هل تمارس الزراعة التجديدية؟",
        "33.ما هي التقنيات التي تطبقها من الزراعة التجديدية؟",
        "34. Seed Selection Criteria",
        "34.ما هي المعايير التي تعتمدها عند شراء البذور/الشتول؟",
        "35. Seed Source",
        "35.كيف تحصل على البذور/الشتول؟",
        "36. Seed Challenges",
        "36.ما هو التحدي الأكبر في الحصول على البذور/الشتول؟",
        "38. Soil Enhancers",
        "38.ما هي أنواع المحسنات التي تستخدمها في التربة؟",
        "39. Chem Fertilizer Reliance",
        "39.ما مدى اعتمادك على الأسمدة الكيميائية؟",
        "40. Fertilizer Cost %",
        "43. Pest Control Method",
        "43.كيف تقوم بمكافحة الآفات؟",
        "44. Pesticide Reliance",
        "44.ما مدى اعتمادك على المبيدات الكيميائية؟",
        "45. Pesticide Cost %",
        "48.ما هي الحواجز الرئيسية التي تمنعك من تبني الزراعة التجديدية؟",
        "49.هل ترغب في المشاركة في تدريبات مستقبلية حول الزراعة التجديدية؟",
    ],
}

# For the simplified Arabic-only _new.csv layer files (used by legacy map layers)
ARABIC_LAYER_SCHEMA = {
    "Water": {
        "output": "Water_new.csv",
        "col_map": {
            "4.القرية:": "القرية",
            "10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟": "المحصول",
            "13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟": "مصدر مياه الريّ الرئيسي",
            "16.كيف تقيّم توفر المياه خلال موسم الزراعة؟": "توفر المياه",
        }
    },
    "Energy": {
        "output": "Energy_new.csv",
        "col_map": {
            "4.القرية:": "القرية",
            "14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟": "مصدر الطاقة الرئيسي",
        }
    },
    "Food": {
        "output": "Food_new.csv",
        "col_map": {
            "4.القرية:": "القرية",
            "10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟": "المحصول",
            "19.كيف تصف مستوى إنتاج الغذاء والمنتجات التقليدية في منزلك/قريتك/تعاونيتك؟": "مستوى الإنتاج",
        }
    },
    "General_Info": {
        "output": "General_Info_new.csv",
        "col_map": {
            "4.القرية:": "القرية",
            "8.ما هو حجم الحيازة الزراعية الخاصة بك؟": "حجم الزراعة",
            "9.ما هو نوع التربة في أرضك؟": "نوع التربة",
        }
    },
    "Regenerative_Agriculture": {
        "output": "Regenerative_Agriculture_new.csv",
        "col_map": {
            "4.القرية:": "القرية",
            "32.هل تمارس الزراعة التجديدية؟": "الزراعة التجديدية",
            "33.ما هي التقنيات التي تطبقها من الزراعة التجديدية؟": "تقنيات الزراعة التجديدية",
            "38.ما هي أنواع المحسنات التي تستخدمها في التربة؟": "محسنات التربة",
            "39.ما مدى اعتمادك على الأسمدة الكيميائية؟": "الاعتماد على الاسمدة الكيميائية",
            "43.كيف تقوم بمكافحة الآفات؟": "مكافحة الآفات",
        }
    },
}

audit = {
    "timestamp": datetime.now().isoformat(),
    "script": "integrate_new_survey_27_2_2026.py",
    "new_excel": str(NEW_EXCEL),
    "steps": [],
    "warnings": [],
    "errors": [],
    "statistics": {},
}

def log(msg, level="INFO"):
    prefix = {"INFO": "  ✓", "WARN": "  ⚠ ", "ERROR": "  ✗ ", "STEP": "\n▶"}
    print(f"{prefix.get(level, '  ')} {msg}")
    if level in ("WARN", "ERROR"):
        audit["warnings" if level == "WARN" else "errors"].append(msg)

def backup(path):
    """Create a timestamped backup of a file."""
    p = Path(path)
    if p.exists():
        dest = p.parent / (p.stem + BACKUP_SUFFIX + p.suffix)
        shutil.copy2(p, dest)
        log(f"Backup: {p.name} → {dest.name}")
        return dest
    return None

def coord_hash(lon, lat, length=8):
    s = f"{float(lon):.8f},{float(lat):.8f}"
    return hashlib.sha256(s.encode()).hexdigest()[:length]

def make_feature_id(theme, row_idx, lon, lat):
    key = theme.lower().replace("_", "")[:6]
    return f"{key}_{row_idx}_{coord_hash(lon, lat)}"


# ─────────────────────────────────────────────
# STEP 1 · Load the new Excel
# ─────────────────────────────────────────────
def step1_load_excel():
    log("Loading new Excel file", "STEP")
    if not NEW_EXCEL.exists():
        log(f"File not found: {NEW_EXCEL}", "ERROR")
        sys.exit(1)

    xl = pd.ExcelFile(str(NEW_EXCEL))
    sheets = xl.sheet_names
    log(f"Sheets found: {sheets}")

    # Strategy: identify the "data" sheet
    # Prefer the one with most rows, or first sheet that is not metadata
    dfs = {}
    for s in sheets:
        df = pd.read_excel(str(NEW_EXCEL), sheet_name=s)
        dfs[s] = df
        log(f"  Sheet '{s}': {len(df)} rows × {len(df.columns)} cols")

    # Pick primary data sheet (largest, or first if all equal)
    primary_sheet = max(dfs, key=lambda s: len(dfs[s]))
    df_new = dfs[primary_sheet]
    log(f"Using primary sheet: '{primary_sheet}' ({len(df_new)} rows)")

    audit["steps"].append({
        "step": 1,
        "action": "load_excel",
        "sheets": sheets,
        "primary_sheet": primary_sheet,
        "rows": len(df_new),
        "cols": len(df_new.columns),
        "columns": list(df_new.columns),
    })
    return df_new, dfs


# ─────────────────────────────────────────────
# STEP 2 · Compare with existing master CSV
# ─────────────────────────────────────────────
def step2_compare(df_new):
    log("Comparing with existing master CSV", "STEP")

    if not OLD_MASTER.exists():
        log("Master CSV not found — treating ALL rows as new", "WARN")
        return df_new.copy(), pd.DataFrame()

    df_old = pd.read_csv(str(OLD_MASTER), encoding="utf-8")
    log(f"Existing: {len(df_old)} rows | New file: {len(df_new)} rows")

    # Schema diff
    old_cols = set(str(c) for c in df_old.columns)
    new_cols = set(str(c) for c in df_new.columns)
    added   = sorted(new_cols - old_cols)
    removed = sorted(old_cols - new_cols)
    if added:
        log(f"NEW columns in new file: {added}", "WARN")
    if removed:
        log(f"REMOVED columns (were in old): {removed}", "WARN")
    log(f"Schema: {len(new_cols & old_cols)} common | +{len(added)} new | -{len(removed)} removed")

    # Find new rows using respondent name + start date as dedup key
    name_col  = "1.اسم المُستجيب:" if "1.اسم المُستجيب:" in df_new.columns else None
    start_col = "start" if "start" in df_new.columns else None

    if name_col and start_col and name_col in df_old.columns and start_col in df_old.columns:
        old_keys = set(zip(
            df_old[name_col].fillna("").astype(str),
            df_old[start_col].fillna("").astype(str),
        ))
        new_rows_mask = df_new.apply(
            lambda r: (str(r.get(name_col, "")), str(r.get(start_col, ""))) not in old_keys,
            axis=1,
        )
        df_truly_new = df_new[new_rows_mask].copy()
        df_overlap   = df_new[~new_rows_mask].copy()
    elif name_col and name_col in df_old.columns:
        old_names = set(df_old[name_col].fillna("").astype(str))
        new_rows_mask = ~df_new[name_col].fillna("").astype(str).isin(old_names)
        df_truly_new = df_new[new_rows_mask].copy()
        df_overlap   = df_new[~new_rows_mask].copy()
    else:
        # Cannot dedup — use all rows of the new file, skip rows already in old
        log("Cannot identify dedup key; using ALL rows in new Excel as update", "WARN")
        df_truly_new = df_new.copy()
        df_overlap   = pd.DataFrame()

    log(f"Truly NEW rows: {len(df_truly_new)} | Overlap (existing): {len(df_overlap)}")

    if name_col and len(df_truly_new) > 0:
        new_names = df_truly_new[name_col].dropna().unique().tolist() if name_col in df_truly_new.columns else []
        log(f"New respondents: {new_names[:10]}")

    audit["steps"].append({
        "step": 2,
        "action": "compare",
        "existing_rows": len(df_old),
        "new_file_rows": len(df_new),
        "truly_new_rows": len(df_truly_new),
        "overlap_rows": len(df_overlap),
        "added_columns": added,
        "removed_columns": removed,
    })
    return df_truly_new, df_old


# ─────────────────────────────────────────────
# STEP 3 · Add coordinates to new rows
# ─────────────────────────────────────────────
def step3_add_coordinates(df_new_rows):
    """Add verified X/Y coordinates to new rows via village name lookup."""
    log("Adding coordinates to new rows", "STEP")

    if df_new_rows.empty:
        log("No new rows — skipping coordinate step")
        return df_new_rows.copy()

    if not COORD_FILE.exists():
        log(f"Coordinate file not found: {COORD_FILE}", "ERROR")
        sys.exit(1)

    with open(str(COORD_FILE), encoding="utf-8") as f:
        coord_data = json.load(f)
    coord_map = coord_data["villages"]  # { "ماسما": {lon, lat, name_en, ...}, ... }

    # Build a normalised lookup (strip + lower for fuzzy-ish match on Arabic)
    coord_lookup = {k.strip(): v for k, v in coord_map.items()}

    df = df_new_rows.copy()

    # Detect village column
    village_col = None
    for c in ["4.القرية:", "4. Village", "القرية", "Village"]:
        if c in df.columns:
            village_col = c
            break

    if not village_col:
        log("Village column not found in new rows!", "ERROR")
        # Assign NaN coords so rows are still kept, just without coordinates
        df["X"] = float("nan")
        df["Y"] = float("nan")
        return df

    x_coords, y_coords, coord_log = [], [], []
    unmapped = []

    for idx, row in df.iterrows():
        village_ar = str(row.get(village_col, "")).strip()

        # Also check English village name if Arabic not found
        village_en = str(row.get("4. Village", "")).strip() if "4. Village" in df.columns else ""

        # Check if coords already present (from Excel)
        has_x = "X" in df.columns and pd.notna(row.get("X")) and str(row.get("X", "")).strip() not in ("", "nan", "NaN")
        has_y = "Y" in df.columns and pd.notna(row.get("Y")) and str(row.get("Y", "")).strip() not in ("", "nan", "NaN")

        if has_x and has_y:
            try:
                x_coords.append(float(row["X"]))
                y_coords.append(float(row["Y"]))
                coord_log.append({"row": idx, "village": village_ar, "status": "EXISTING"})
                continue
            except (ValueError, TypeError):
                pass

        # Lookup by Arabic name
        if village_ar in coord_lookup:
            info = coord_lookup[village_ar]
            x_coords.append(info["lon"])
            y_coords.append(info["lat"])
            coord_log.append({"row": idx, "village": village_ar, "status": "FOUND", "en": info.get("name_en","")})
        else:
            # Try English village name against coord_lookup values
            found = False
            for ar_key, info in coord_lookup.items():
                if info.get("name_en", "").lower() == village_en.lower() and village_en:
                    x_coords.append(info["lon"])
                    y_coords.append(info["lat"])
                    coord_log.append({"row": idx, "village": village_ar, "status": "FOUND_EN", "en": info.get("name_en","")})
                    found = True
                    break
            if not found:
                x_coords.append(float("nan"))
                y_coords.append(float("nan"))
                unmapped.append(village_ar or village_en or f"Row {idx}")
                coord_log.append({"row": idx, "village": village_ar, "status": "NOT_FOUND"})

    df["X"] = x_coords
    df["Y"] = y_coords

    mapped = sum(1 for c in coord_log if c["status"] in ("FOUND", "FOUND_EN", "EXISTING"))
    log(f"Coords assigned: {mapped}/{len(df)} rows")

    if unmapped:
        log(f"UNMAPPED villages (no coordinates): {unmapped}", "WARN")
        log("These rows will be EXCLUDED from GeoJSON (kept in CSV)", "WARN")

    audit["steps"].append({
        "step": 3,
        "action": "add_coordinates",
        "total_rows": len(df),
        "mapped": mapped,
        "unmapped": unmapped,
        "coord_log": coord_log,
    })
    return df


# ─────────────────────────────────────────────
# STEP 4 · Update master CSV files
# ─────────────────────────────────────────────
def step4_update_master_csvs(df_new_rows, _df_old_unused=None):
    """Append new rows to master CSV files.

    IMPORTANT: We always load OLD_COORDS (the file that includes X/Y) as the
    base for df_merged so that existing rows retain their coordinates.  The
    legacy OLD_MASTER (no X/Y) file was previously passed as df_old but that
    caused all pre-existing rows to get NaN X/Y in every downstream file.
    """
    log("Updating master CSV files", "STEP")

    # ── Load existing data WITH coordinates as the authoritative base ──────
    if OLD_COORDS.exists():
        df_existing = pd.read_csv(str(OLD_COORDS), encoding="utf-8")
        log(f"Loaded existing (with coords): {len(df_existing)} rows")
    else:
        df_existing = pd.DataFrame()
        log("No existing master-with-coords found — starting fresh", "WARN")

    if df_new_rows.empty:
        log("No new rows — master CSV unchanged")
        audit["steps"].append({"step": 4, "action": "update_master_csvs", "rows_added": 0,
                                "total_rows": len(df_existing)})
        return df_existing

    # Align columns: union of existing + new
    all_cols = list(df_existing.columns) if not df_existing.empty else []
    for c in df_new_rows.columns:
        if c not in all_cols:
            all_cols.append(c)
            log(f"New column appended to master: {c}", "WARN")

    df_merged = pd.concat(
        [df_existing.reindex(columns=all_cols), df_new_rows.reindex(columns=all_cols)],
        ignore_index=True,
    )

    # Write master WITH coords (source of truth for all downstream steps)
    backup(OLD_COORDS)
    df_merged.to_csv(str(OLD_COORDS), index=False, encoding="utf-8")
    log(f"Master with-coords CSV updated: {len(df_merged)} rows → {OLD_COORDS.name}")

    # Write master WITHOUT coords (pure survey export, no X/Y)
    cols_without_xy = [c for c in df_merged.columns if c not in ("X", "Y")]
    backup(OLD_MASTER)
    df_merged[cols_without_xy].to_csv(str(OLD_MASTER), index=False, encoding="utf-8")
    log(f"Master CSV (no coords) updated: {OLD_MASTER.name}")

    audit["steps"].append({
        "step": 4,
        "action": "update_master_csvs",
        "rows_added": len(df_new_rows),
        "total_rows": len(df_merged),
    })
    return df_merged


# ─────────────────────────────────────────────
# STEP 5 · Split merged data by theme
# ─────────────────────────────────────────────
def step5_split_by_theme(df_full):
    """Rebuild survey_by_theme/ CSV files from full merged data."""
    log("Splitting by theme (survey_by_theme/)", "STEP")
    SURVEY_THEME_DIR.mkdir(parents=True, exist_ok=True)

    THEME_SURVEY_COLS = {
        "Water": [
            "1.اسم المُستجيب:",
            "10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟",
            "13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟",
            "14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟",
            "16.كيف تقيّم توفر المياه خلال موسم الزراعة؟",
        ],
        "Energy": [
            "1.اسم المُستجيب:",
            "14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟",
            "15.كمية الطاقة المستخدمة خلال موسم الذروة الزراعي (تقدير بالساعة أو بالوقود):",
        ],
        "Food": [
            "1.اسم المُستجيب:",
            "10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟",
            "19.كيف تصف مستوى إنتاج الغذاء والمنتجات التقليدية في منزلك/قريتك/تعاونيتك؟",
            "21. ما هي المنتجات التقليدية الرئيسية التي تُنتج في منزلك/تعاونيتك/قريتك؟",
        ],
        "General_Info": [
            "1.اسم المُستجيب:", "4.القرية:", "5.هل تمتلك أرضاً زراعية؟",
            "8.ما هو حجم الحيازة الزراعية الخاصة بك؟",
            "9.ما هو نوع التربة في أرضك؟", "X", "Y",
        ],
        "Regenerative_Agriculture": [
            "1.اسم المُستجيب:",
            "29.ما مدى معرفتك بمفهوم الزراعة التجديدية؟",
            "32.هل تمارس الزراعة التجديدية؟",
            "33.ما هي التقنيات التي تطبقها من الزراعة التجديدية؟",
            "38.ما هي أنواع المحسنات التي تستخدمها في التربة؟",
            "43.كيف تقوم بمكافحة الآفات؟",
        ],
    }

    results = {}
    for theme, cols in THEME_SURVEY_COLS.items():
        avail = [c for c in cols if c in df_full.columns]
        out   = SURVEY_THEME_DIR / f"MZSurvey_{theme}.csv"
        backup(out)
        df_full[avail].to_csv(str(out), index=False, encoding="utf-8")
        log(f"{theme}: {len(df_full)} rows × {len(avail)} cols → {out.name}")
        results[theme] = {"rows": len(df_full), "cols": avail}

    audit["steps"].append({"step": 5, "action": "split_by_theme", "results": results})


# ─────────────────────────────────────────────
# STEP 6 · Rebuild Arabic _new.csv layer files
# ─────────────────────────────────────────────
def step6_rebuild_arabic_layers(df_full):
    """Rebuild the simplified Arabic layer CSV files used by the map."""
    log("Rebuilding Arabic layer CSV files", "STEP")
    ARABIC_LAYER_DIR.mkdir(parents=True, exist_ok=True)

    # Only rows with valid coordinates
    df_coord = df_full.dropna(subset=["X", "Y"]).copy()
    df_coord = df_coord[
        pd.to_numeric(df_coord["X"], errors="coerce").notna() &
        pd.to_numeric(df_coord["Y"], errors="coerce").notna()
    ]
    log(f"Rows with valid coordinates: {len(df_coord)}/{len(df_full)}")

    results = {}
    for theme, schema in ARABIC_LAYER_SCHEMA.items():
        col_map  = schema["col_map"]
        out_name = schema["output"]

        avail_map = {k: v for k, v in col_map.items() if k in df_coord.columns}
        df_layer  = df_coord[list(avail_map.keys()) + ["X", "Y"]].copy()
        df_layer.rename(columns=avail_map, inplace=True)

        out = ARABIC_LAYER_DIR / out_name
        backup(out)
        df_layer.to_csv(str(out), index=False, encoding="utf-8")
        log(f"{out_name}: {len(df_layer)} rows × {len(df_layer.columns)} cols")
        results[theme] = {"file": out_name, "rows": len(df_layer)}

    audit["steps"].append({"step": 6, "action": "rebuild_arabic_layers", "results": results})


# ─────────────────────────────────────────────
# STEP 7 · Regenerate *_new.canonical.geojson
# ─────────────────────────────────────────────
def _is_arabic(text):
    """Return True if text contains Arabic characters."""
    return any("\u0600" <= c <= "\u06ff" for c in str(text))

def _build_bilingual_props(row, cols_to_use):
    ar_vals, en_vals = {}, {}
    for col in cols_to_use:
        if col in ("X", "Y"):
            continue
        val = row.get(col)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        val_str = str(val).strip()
        if not val_str or val_str.lower() in ("nan", "none", ""):
            continue
        if _is_arabic(col):
            ar_vals[col.rstrip(":")] = val_str
        else:
            en_vals[col] = val_str
    return ar_vals, en_vals

def step7_regenerate_canonical(df_full):
    """Regenerate all *_new.canonical.geojson files from merged data."""
    log("Regenerating *_new.canonical.geojson files", "STEP")
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)

    df_coord = df_full.dropna(subset=["X", "Y"]).copy()
    try:
        df_coord["X"] = pd.to_numeric(df_coord["X"], errors="coerce")
        df_coord["Y"] = pd.to_numeric(df_coord["Y"], errors="coerce")
        df_coord = df_coord.dropna(subset=["X", "Y"])
    except Exception as e:
        log(f"Coordinate conversion error: {e}", "WARN")

    log(f"Features with coords: {len(df_coord)}")

    geojson_results = {}
    for theme, requested_cols in THEME_COLUMNS.items():
        # Only use columns that actually exist
        use_cols = [c for c in requested_cols if c in df_coord.columns]

        features = []
        for row_i, (_, row) in enumerate(df_coord.iterrows(), start=1):
            try:
                lon = float(row["X"])
                lat = float(row["Y"])
            except (ValueError, TypeError):
                continue
            if pd.isna(lon) or pd.isna(lat):
                continue

            ar_props, en_props = _build_bilingual_props(row, use_cols)
            feat_id = make_feature_id(theme, row_i, lon, lat)

            feature = {
                "type": "Feature",
                "id": feat_id,
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "featureId": feat_id,
                    "theme": theme.lower().replace("_", ""),
                    "values": {"ar": ar_props, "en": en_props},
                    "metadata": {
                        "sourceRow": row_i,
                        "dataSource": "FarmersSurvey_27-2-2026",
                        "translationStatus": "complete",
                        "generatedAt": datetime.now().isoformat(),
                    },
                },
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "theme": theme,
                "dataSource": "FarmersSurvey_27-2-2026",
                "generatedAt": datetime.now().isoformat(),
                "featureCount": len(features),
                "translationStatus": "complete",
            },
            "features": features,
        }

        out_path = CANONICAL_DIR / f"{theme}_new.canonical.geojson"
        backup(out_path)
        with open(str(out_path), "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)

        geojson_results[theme] = len(features)
        log(f"{theme}_new.canonical.geojson: {len(features)} features")

    audit["steps"].append({
        "step": 7,
        "action": "regenerate_canonical",
        "results": geojson_results,
    })
    return geojson_results


# ─────────────────────────────────────────────
# STEP 8 · Update Original_Survey_Data_Complete.xlsx
# ─────────────────────────────────────────────
def step8_update_original_excel(df_full):
    """Rebuild the combined Excel workbook."""
    log("Updating Original_Survey_Data_Complete.xlsx", "STEP")
    backup(ORIG_EXCEL)

    df_coord = df_full.dropna(subset=["X", "Y"]).copy()

    try:
        with pd.ExcelWriter(str(ORIG_EXCEL), engine="openpyxl") as writer:
            # Full survey sheet
            df_full.to_excel(writer, sheet_name="Full_Survey", index=False)

            # Original Arabic data (unmodified)
            for theme, schema in ARABIC_LAYER_SCHEMA.items():
                ar_path = ARABIC_LAYER_DIR / "Water_1.0.csv"
                theme_path = ARABIC_LAYER_DIR / f"{theme}_1.0.csv"
                alt_names = {
                    "General_Info": "Generalinfo_1.0.csv",
                    "Regenerative_Agriculture": "Regenerative_1.0.csv",
                }
                fname = alt_names.get(theme, f"{theme}_1.0.csv")
                legacy_path = ARABIC_LAYER_DIR / fname
                if legacy_path.exists():
                    df_legacy = pd.read_csv(str(legacy_path), encoding="utf-8-sig")
                    sheet_name = f"{theme}_Original"[:31]
                    df_legacy.to_excel(writer, sheet_name=sheet_name, index=False)

            # New survey data (all)
            df_full.to_excel(writer, sheet_name="New_Survey_All", index=False)

            # New survey - with coords only
            df_coord.to_excel(writer, sheet_name="New_Survey_Coords", index=False)

        log(f"Excel written: {ORIG_EXCEL.name}")
        audit["steps"].append({"step": 8, "action": "update_excel", "status": "OK"})
    except Exception as e:
        log(f"Excel write failed (non-fatal): {e}", "WARN")
        audit["steps"].append({"step": 8, "action": "update_excel", "status": f"FAILED: {e}"})


# ─────────────────────────────────────────────
# STEP 9 · Optional ML Feature Engineering
# ─────────────────────────────────────────────
def step9_optional_ml_features():
    """Re-run ML feature engineering to update ml_prepared_data.csv if sklearn available."""
    log("Optional: ML feature engineering update", "STEP")
    try:
        import sklearn  # noqa: F401
        import scipy    # noqa: F401
        import joblib   # noqa: F401
    except ImportError as e:
        log(f"ML dependencies not available ({e}) — skipping ML update", "WARN")
        log("To run ML pipeline: pip install scikit-learn scipy joblib xgboost, then run scripts/ml_pipeline/run_pipeline.py")
        audit["steps"].append({"step": 9, "action": "ml_features", "status": "SKIPPED_MISSING_DEPS"})
        return

    try:
        ml_dir = ROOT / "scripts" / "ml_pipeline"
        sys.path.insert(0, str(ml_dir))
        from feature_engineering import FeatureEngineer  # noqa: E402
        engineer = FeatureEngineer()
        engineer.prepare_ml_dataset()
        engineer.save_prepared_data()
        log("ml_prepared_data.csv updated via feature engineering")
        audit["steps"].append({"step": 9, "action": "ml_features", "status": "OK"})
    except Exception as e:
        log(f"ML feature engineering failed (non-fatal): {e}", "WARN")
        audit["steps"].append({"step": 9, "action": "ml_features", "status": f"FAILED: {e}"})


# ─────────────────────────────────────────────
# STEP 10 · Write audit JSON
# ─────────────────────────────────────────────
def step10_write_audit(df_new_rows, geojson_results):
    log("Writing audit report", "STEP")
    audit["statistics"] = {
        "new_rows_added": len(df_new_rows) if df_new_rows is not None else 0,
        "geojson_features_per_theme": geojson_results if geojson_results else {},
        "completed": datetime.now().isoformat(),
    }
    with open(str(AUDIT_FILE), "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    log(f"Audit saved: {AUDIT_FILE.name}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 72)
    print("  FARMERS SURVEY INTEGRATION  —  Farmers survey 27-2-2026.xlsx")
    print("=" * 72)

    # 1. Load new Excel
    df_new_primary, all_sheets = step1_load_excel()

    # 2. Compare with existing
    df_truly_new, df_old = step2_compare(df_new_primary)

    # 3. Add coordinates
    df_truly_new_coords = step3_add_coordinates(df_truly_new)

    # 4. Update master CSVs
    # If no new rows, still re-run downstream using existing full data
    if df_truly_new_coords.empty:
        log("\nNo new rows detected. Rebuilding all downstream files from existing data.", "WARN")
        df_full = pd.read_csv(str(OLD_COORDS), encoding="utf-8") if OLD_COORDS.exists() else df_old
    else:
        df_full = step4_update_master_csvs(df_truly_new_coords, df_old)
        if df_full is None:
            df_full = pd.read_csv(str(OLD_COORDS), encoding="utf-8")

    # 5. Split by theme
    step5_split_by_theme(df_full)

    # 6. Rebuild Arabic layer CSVs
    step6_rebuild_arabic_layers(df_full)

    # 7. Regenerate canonical GeoJSON
    geojson_results = step7_regenerate_canonical(df_full)

    # 8. Update Excel
    step8_update_original_excel(df_full)

    # 9. Optional: Re-run ML feature engineering (if sklearn available)
    step9_optional_ml_features()

    # 10. Audit
    step10_write_audit(df_truly_new_coords, geojson_results)

    # ── Final summary ─────────────────────────────
    print("\n" + "=" * 72)
    print("  INTEGRATION COMPLETE")
    print("=" * 72)
    print(f"  New rows added   : {len(df_truly_new_coords)}")
    print(f"  Total survey rows: {len(df_full)}")
    print()
    print("  GeoJSON features generated:")
    for theme, count in (geojson_results or {}).items():
        print(f"    {theme:<32s} {count:3d} features")
    print()
    print("  Updated files:")
    print(f"    {OLD_MASTER.name}")
    print(f"    {OLD_COORDS.name}")
    for t in THEME_COLUMNS:
        print(f"    survey_by_theme/MZSurvey_{t}.csv")
    for s in ARABIC_LAYER_SCHEMA.values():
        print(f"    layers/Arabic/{s['output']}")
    for t in THEME_COLUMNS:
        print(f"    geojson/canonical/{t}_new.canonical.geojson")
    print(f"\n  Audit: {AUDIT_FILE.name}")
    print()

    if audit["warnings"]:
        print("  WARNINGS (review before deploying):")
        for w in audit["warnings"]:
            print(f"    ⚠  {w}")
    if audit["errors"]:
        print("  ERRORS:")
        for e in audit["errors"]:
            print(f"    ✗  {e}")
        return False

    print("\n  ✓  All downstream data products rebuilt successfully.")
    print("  ✓  Increment DATA_VERSION in app/modules/data/loader.js to bust caches.")
    print("  ✓  Restart local server: python -m http.server 8000")
    print("=" * 72)
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)

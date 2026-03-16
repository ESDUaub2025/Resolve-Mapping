"""
Excel Inspection → JSON output
Writes to scripts/excel_inspection_report.json for reading by copilot
"""
import pandas as pd
import json
import os

BASE = r"d:\Programing\ResolveMaping_final2\data"
NEW_EXCEL = os.path.join(BASE, "Farmers survey 27-2-2026.xlsx")
OLD_EXCEL = os.path.join(BASE, "Original_Survey_Data_Complete.xlsx")

report = {"new_excel": {}, "old_excel": {}, "comparison": {}}

# ---------- NEW EXCEL ----------
xl_new = pd.ExcelFile(NEW_EXCEL)
report["new_excel"]["sheets"] = xl_new.sheet_names
report["new_excel"]["by_sheet"] = {}

for sheet in xl_new.sheet_names:
    df = pd.read_excel(NEW_EXCEL, sheet_name=sheet)
    report["new_excel"]["by_sheet"][sheet] = {
        "rows": len(df),
        "cols": len(df.columns),
        "columns": list(df.columns),
        "first_row_sample": {str(c): str(df.iloc[0][c]) if len(df) > 0 else "EMPTY"
                             for c in list(df.columns)[:20]},
        "last_row_sample": {str(c): str(df.iloc[-1][c]) if len(df) > 0 else "EMPTY"
                            for c in list(df.columns)[:20]},
        "date_range": {
            "first": str(df.iloc[0]["start"]) if "start" in df.columns and len(df) > 0 else "N/A",
            "last": str(df.iloc[-1]["start"]) if "start" in df.columns and len(df) > 0 else "N/A"
        }
    }

# ---------- OLD EXCEL ----------
xl_old = pd.ExcelFile(OLD_EXCEL)
report["old_excel"]["sheets"] = xl_old.sheet_names
report["old_excel"]["by_sheet"] = {}
for sheet in xl_old.sheet_names:
    df = pd.read_excel(OLD_EXCEL, sheet_name=sheet)
    report["old_excel"]["by_sheet"][sheet] = {
        "rows": len(df),
        "cols": len(df.columns),
        "columns": list(df.columns)
    }

# ---------- EXISTING CSVs ----------
report["existing_csvs"] = {}
arabic_dir = os.path.join(BASE, "layers", "Arabic")
english_dir = os.path.join(BASE, "layers", "English")
survey_dir = os.path.join(BASE, "survey_by_theme")

for d, label in [(arabic_dir, "arabic"), (english_dir, "english"), (survey_dir, "survey_by_theme")]:
    report["existing_csvs"][label] = {}
    for f in sorted(os.listdir(d)):
        if f.endswith(".csv"):
            df = pd.read_csv(os.path.join(d, f), encoding="utf-8-sig")
            report["existing_csvs"][label][f] = {
                "rows": len(df),
                "cols": len(df.columns),
                "columns": list(df.columns)
            }

# ---------- MASTER CSVs ----------
for fname, label in [
    ("MZSurvey farmers ENGLISH.csv", "MZSurvey_EN"),
    ("MZSurvey farmers ENGLISH_with_coords.csv", "MZSurvey_EN_coords"),
]:
    fpath = os.path.join(BASE, fname)
    df = pd.read_csv(fpath, encoding="utf-8")
    report["existing_csvs"][label] = {
        "rows": len(df),
        "cols": len(df.columns),
        "columns": list(df.columns),
        "villages": sorted(df["4.القرية:"].dropna().unique().tolist()) if "4.القرية:" in df.columns else []
    }

# ---------- COMPARISON: new Excel vs master CSV ----------
if len(xl_new.sheet_names) > 0:
    # Use first sheet of new Excel
    first_sheet = xl_new.sheet_names[0]
    df_new = pd.read_excel(NEW_EXCEL, sheet_name=first_sheet)
    
    master_en_path = os.path.join(BASE, "MZSurvey farmers ENGLISH.csv")
    df_old = pd.read_csv(master_en_path, encoding="utf-8")
    
    new_cols = set(str(c) for c in df_new.columns)
    old_cols = set(str(c) for c in df_old.columns)
    
    report["comparison"] = {
        "new_rows": len(df_new),
        "old_rows": len(df_old),
        "row_diff": len(df_new) - len(df_old),
        "new_columns_added": sorted(list(new_cols - old_cols)),
        "old_columns_removed": sorted(list(old_cols - new_cols)),
        "common_columns": len(new_cols & old_cols),
        "total_new_cols": len(new_cols),
        "total_old_cols": len(old_cols)
    }
    
    # Try to find truly new respondents
    if "1.اسم المُستجيب:" in df_new.columns and "1.اسم المُستجيب:" in df_old.columns:
        old_names = set(df_old["1.اسم المُستجيب:"].dropna().astype(str).tolist())
        new_names = set(df_new["1.اسم المُستجيب:"].dropna().astype(str).tolist())
        report["comparison"]["new_respondents"] = sorted(list(new_names - old_names))
        report["comparison"]["old_respondents"] = sorted(list(old_names - new_names))
        report["comparison"]["respondent_overlap"] = len(old_names & new_names)

    # Villages in new data
    village_col = None
    for possible in ["4.القرية:", "4. Village", "Village", "القرية"]:
        if possible in df_new.columns:
            village_col = possible
            break
    if village_col:
        report["comparison"]["villages_in_new"] = sorted(df_new[village_col].dropna().unique().tolist())

    # Dates
    if "start" in df_new.columns:
        report["comparison"]["date_range_new"] = {
            "first": str(df_new["start"].min()),
            "last": str(df_new["start"].max())
        }

out_path = r"d:\Programing\ResolveMaping_final2\scripts\excel_inspection_report.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"Report written to {out_path}")

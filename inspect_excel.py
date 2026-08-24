from pathlib import Path
import pandas as pd

CORE_DIR = Path("data/raw/core")
SUPP_DIR = Path("data/raw/supplementary")

def inspect_folder(folder, header):
    print(f"\n{'=' * 80}")
    print(f"FOLDER: {folder}")
    print(f"{'=' * 80}")

    for file in sorted(folder.glob("*.xlsx")):
        print(f"\nFILE: {file.name}")

        excel_file = pd.ExcelFile(file)
        print("Sheets:", excel_file.sheet_names)

        for sheet in excel_file.sheet_names:
            df = pd.read_excel(file, sheet_name=sheet, header=header)

            print(f"  Sheet: {sheet}")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            print("  First 2 rows:")
            print(df.head(2).to_string(index=False))
            print("-" * 80)

print("\nCORE DATASETS")
inspect_folder(CORE_DIR, header=1)

print("\nSUPPLEMENTARY DATASETS")
inspect_folder(SUPP_DIR, header=0)
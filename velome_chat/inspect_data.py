import pandas as pd
import os

DATA_DIR = r"c:\Users\ashmi\Videos\Velome\velome_chat\data"
excel_file = os.path.join(DATA_DIR, "Destinations List Countries and Regions with details.xlsx")
ods_file = os.path.join(DATA_DIR, "Selling Price list - Countries & Regions.ods")

def inspect_file(filepath):
    print(f"\n--- Inspecting {os.path.basename(filepath)} ---")
    try:
        if filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        elif filepath.endswith('.ods'):
            df = pd.read_excel(filepath, engine="odf") # pandas uses odfpy for ods
        
        print("Columns:", df.columns.tolist())
        print("First 3 rows:")
        print(df.head(3).to_string())
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

if os.path.exists(excel_file):
    inspect_file(excel_file)
else:
    print(f"File not found: {excel_file}")

if os.path.exists(ods_file):
    inspect_file(ods_file)
else:
    print(f"File not found: {ods_file}")

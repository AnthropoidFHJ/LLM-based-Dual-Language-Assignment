import os
import pandas as pd

def clean_excel_file(input_file, output_file):
    """
    Cleans all sheets of an Excel file by removing empty rows/columns,
    non-tabular content, and saves the combined clean data to a new Excel file.

    Args:
        input_file (str): Path to the original Excel file
        output_file (str): Path where cleaned Excel file will be saved
    """
    xl = pd.ExcelFile(input_file)
    print(f"[INFO] Found sheets: {xl.sheet_names}")

    writer = pd.ExcelWriter(output_file, engine='openpyxl')

    for sheet_name in xl.sheet_names:
        try:
            df = xl.parse(sheet_name)

            # Drop empty rows/columns
            df.dropna(axis=0, how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)

            # Drop weak rows (very sparse)
            df = df[df.count(axis=1) > 2]

            # Clean up column names
            df.columns = [str(col).strip() for col in df.columns]
            df = df.loc[:, ~df.columns.str.contains('Unnamed', na=False)]

            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                print(f"[✓] Cleaned sheet '{sheet_name}' added to {output_file}")
            else:
                print(f"[!] Sheet '{sheet_name}' empty after cleaning. Skipped.")

        except Exception as e:
            print(f"[x] Failed to clean sheet '{sheet_name}': {e}")

    writer.close()
    print(f"\n[✔] All cleaned sheets saved to: {output_file}")

if __name__ == "__main__":
    INPUT_PATH = "data/JMP_WASH_Data.xlsx"
    OUTPUT_PATH = "data/cleaned_Data.xlsx"

    clean_excel_file(INPUT_PATH, OUTPUT_PATH)

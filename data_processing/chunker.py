import os
import sys
import pandas as pd

def chunk_excel_data(cleaned_file, chunk_size=100):
    """
    Reads cleaned Excel sheets and breaks data into text chunks.

    Args:
        cleaned_file (str): Path to cleaned Excel file
        chunk_size (int): Maximum number of words per chunk

    Returns:
        List of textual chunks
    """
    if not os.path.exists(cleaned_file):
        raise FileNotFoundError(f"❌ '{cleaned_file}' not found. Run the cleaner first.")

    xl = pd.ExcelFile(cleaned_file)
    all_chunks = []

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)
        df.dropna(how='all', axis=0, inplace=True)
        df.dropna(how='all', axis=1, inplace=True)

        if df.empty:
            print(f"⚠️ Sheet '{sheet_name}' is empty after cleaning. Skipping.")
            continue

        print(f"📄 Chunking sheet: {sheet_name} ({len(df)} rows)")

        for _, row in df.iterrows():
            text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
            if text:
                all_chunks.append(text)

    # Split into ~chunk_size-word blocks
    final_chunks = []
    temp = ""
    for chunk in all_chunks:
        if len(temp.split()) + len(chunk.split()) <= chunk_size:
            temp += " " + chunk
        else:
            final_chunks.append(temp.strip())
            temp = chunk
    if temp:
        final_chunks.append(temp.strip())

    return final_chunks

def save_chunks_to_file(chunks, output_file="data/chunks.txt"):
    """Write formatted chunks to file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(f"[Chunk {i+1}]\n{chunk}\n\n")
    print(f"[✔] Saved {len(chunks)} chunks to {output_file}")

if __name__ == "__main__":
    cleaned_path = "data/cleaned_Data.xlsx"
    chunk_output = "data/chunks.txt"
    chunk_size = 100  # or get from CLI if you want flexibility

    try:
        print(f"🔍 Loading cleaned Excel file: {cleaned_path}")
        chunks = chunk_excel_data(cleaned_path, chunk_size)
        save_chunks_to_file(chunks, chunk_output)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

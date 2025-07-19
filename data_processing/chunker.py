import os
import pandas as pd

def thematic_chunk_excel(cleaned_file, chunk_size=100):
    if not os.path.exists(cleaned_file):
        raise FileNotFoundError(f"'{cleaned_file}' not found.")

    xl = pd.ExcelFile(cleaned_file)
    all_chunks = []

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name).dropna(how='all').dropna(axis=1, how='all')
        if df.empty:
            continue
        if 'Topic' in df.columns:
            for topic, group in df.groupby('Topic'):
                text = "\n".join([
                    " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                    for _, row in group.iterrows()
                ])
                if text:
                    all_chunks.append({'text': text, 'topic': topic, 'sheet': sheet_name})
        else:
            for _, row in df.iterrows():
                text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                if text:
                    all_chunks.append({'text': text, 'topic': None, 'sheet': sheet_name})

    final_chunks = []
    temp = ""
    temp_meta = None
    for chunk in all_chunks:
        if temp_meta is None:
            temp_meta = chunk
        if len(temp.split()) + len(chunk['text'].split()) <= chunk_size and (temp_meta['topic'] == chunk['topic']):
            temp += " " + chunk['text']
        else:
            if temp:
                final_chunks.append({'text': temp.strip(), 'topic': temp_meta['topic'], 'sheet': temp_meta['sheet']})
            temp = chunk['text']
            temp_meta = chunk
    if temp:
        final_chunks.append({'text': temp.strip(), 'topic': temp_meta['topic'], 'sheet': temp_meta['sheet']})

    for i, c in enumerate(final_chunks):
        print(f"[Chunk {i+1}] Topic: {c['topic']} | Sheet: {c['sheet']} | Words: {len(c['text'].split())}")

    return final_chunks

def save_chunks_to_file(chunks, output_file="data/chunks.txt"):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(f"[Chunk {i+1}] Topic: {chunk['topic']} | Sheet: {chunk['sheet']}\n{chunk['text']}\n\n")
    print(f"Saved {len(chunks)} chunks to {output_file}")

if __name__ == "__main__":
    cleaned_path = "data/cleaned_Data.xlsx"
    chunk_output = "data/chunks.txt"
    chunk_size = 100

    try:
        chunks = thematic_chunk_excel(cleaned_path, chunk_size)
        save_chunks_to_file(chunks, chunk_output)
    except Exception as e:
        print(e)
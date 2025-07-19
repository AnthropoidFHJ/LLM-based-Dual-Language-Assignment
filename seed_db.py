import os
import sys
from config import Config
from data_processing.data_cleaner import load_and_clean_excel
from data_processing.chunker import chunk_dataframe
from pinecone_db.pinecone_setup import init_pinecone_index, upsert_chunks
from pinecone_db.embeddings import get_embedding_dim, embed_chunks

def ingest_excel(path: str, chunk_size: int = 100):
    """Load an Excel file, clean and chunk it, embed, and upsert into Pinecone."""
    print(f"\n📄 Loading Excel file: {path}")
    sheets = load_and_clean_excel(path)
    if not sheets:
        print("❌ No sheets found after cleaning.")
        return

    print(f"✅ Found sheets: {list(sheets.keys())}")

    # Initialize Pinecone index
    index_name = Config.PINECONE_INDEX_NAME
    dim = get_embedding_dim()
    index = init_pinecone_index(dimension=dim)
    print(f"📦 Pinecone index '{index_name}' initialized with dim={dim}")

    total_chunks = 0
    for sheet_name, df in sheets.items():
        print(f"\n📊 Processing sheet: {sheet_name}")
        chunks = chunk_dataframe(df, sheet_name, chunk_size)
        if not chunks:
            print(f"⚠️  No chunks created for sheet '{sheet_name}'. Skipping.")
            continue

        embeddings = embed_chunks(chunks)
        upsert_chunks(index, chunks, embeddings)
        print(f"  • {len(chunks)} chunks upserted for '{sheet_name}'")
        total_chunks += len(chunks)

    print(f"\n✅ Done! {total_chunks} total chunks uploaded to '{index_name}'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_db.py path/to/JMP_WASH_Data.xlsx [chunk_size]")
        sys.exit(1)

    excel_path = sys.argv[1]
    if not os.path.isfile(excel_path):
        print(f"❌ Error: File not found: {excel_path}")
        sys.exit(1)

    # Optional: custom chunk size from CLI
    try:
        chunk_size = int(sys.argv[2]) if len(sys.argv) == 3 else 100
    except ValueError:
        print("❌ Invalid chunk size. Must be an integer.")
        sys.exit(1)

    ingest_excel(excel_path, chunk_size)

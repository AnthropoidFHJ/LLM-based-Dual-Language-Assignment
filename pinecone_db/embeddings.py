import os
import sys
import re
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

PINECONE_API_KEY = Config.PINECONE_API_KEY
PINECONE_ENV = Config.PINECONE_ENV
INDEX_NAME = Config.PINECONE_INDEX_NAME
MODEL_NAME = Config.EMBEDDING_MODEL

model = SentenceTransformer(MODEL_NAME)
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

if INDEX_NAME not in pinecone_client.list_indexes().names():
    print(f"Creating index '{INDEX_NAME}'...")
    pinecone_client.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )
else:
    print(f"Index '{INDEX_NAME}' already exists.")

index = pinecone_client.Index(INDEX_NAME)

def get_embedding(text):
    return model.encode(text).tolist()

def parse_chunk_block(block):
    lines = block.strip().split('\n', 1)
    if len(lines) < 2:
        return None
    header, text = lines
    match = re.match(r"\[Chunk \d+\] Topic: (.*?) \| Sheet: (.*)", header)
    topic = match.group(1) if match else None
    sheet = match.group(2) if match else None
    return {
        "text": text.strip(),
        "topic": topic,
        "sheet": sheet
    }

def upload_chunks_to_pinecone(chunks_file, batch_size=100):
    if not os.path.exists(chunks_file):
        print(f"File not found: {chunks_file}")
        return

    with open(chunks_file, "r", encoding="utf-8") as f:
        raw = f.read().strip().split("\n\n")
        vectors = []
        for i, block in enumerate(raw):
            if not block.strip():
                continue
            parsed = parse_chunk_block(block)
            if not parsed:
                print(f"Skipping malformed chunk at index {i}")
                continue
            print(f"Embedding chunk-{i}: {parsed['text'][:60]}...")
            try:
                vector = get_embedding(parsed['text'])
                meta = {"text": parsed['text']}
                if parsed['topic']:
                    meta["topic"] = parsed['topic']
                if parsed['sheet']:
                    meta["sheet"] = parsed['sheet']
                vectors.append((f"chunk-{i}", vector, meta))
            except Exception as e:
                print(f"Error embedding chunk-{i}: {e}")
                continue

            if len(vectors) >= batch_size:
                try:
                    index.upsert(vectors)
                    print(f"Upserted {len(vectors)} vectors.")
                except Exception as e:
                    print(f"Error upserting batch: {e}")
                vectors = []

        if vectors:
            try:
                index.upsert(vectors)
                print(f"Upserted {len(vectors)} vectors.")
            except Exception as e:
                print(f"Error upserting final batch: {e}")

    print(f"\nUploaded all chunks to Pinecone index '{INDEX_NAME}'.")

if __name__ == "__main__":
    upload_chunks_to_pinecone("data/chunks.txt")
    print("Done uploading chunks.")
import os
import sys
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Add project root to sys.path (for relative imports to work)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

# Load config values
PINECONE_API_KEY = Config.PINECONE_API_KEY
PINECONE_ENV = Config.PINECONE_ENV
INDEX_NAME = Config.PINECONE_INDEX_NAME
MODEL_NAME = Config.EMBEDDING_MODEL

# Load SentenceTransformer model
model = SentenceTransformer(MODEL_NAME)

# Pinecone client setup
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

# Ensure Pinecone index exists
if INDEX_NAME not in pinecone_client.list_indexes().names():
    pinecone_client.create_index(
        name=INDEX_NAME,
        dimension=384,  # all-MiniLM-L6-v2 outputs 384 dims
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )

index = pinecone_client.Index(INDEX_NAME)

def get_embedding(text):
    """Generate an embedding using SentenceTransformers."""
    return model.encode(text).tolist()

def upload_chunks_to_pinecone(chunks_file):
    """Read text chunks from file and upload to Pinecone with embeddings."""
    if not os.path.exists(chunks_file):
        print(f"❌ File not found: {chunks_file}")
        return

    with open(chunks_file, "r", encoding="utf-8") as f:
        raw = f.read().split("\n\n")
        vectors = []
        for i, block in enumerate(raw):
            if not block.strip():
                continue
            text = block.split("]", 1)[-1].strip()
            print(f"🔢 Embedding chunk-{i}: {text[:60]}...")

            vector = get_embedding(text)
            vectors.append((f"chunk-{i}", vector, {"text": text}))

    index.upsert(vectors)
    print(f"\n[✔] Uploaded {len(vectors)} chunks to Pinecone index '{INDEX_NAME}'.")

if __name__ == "__main__":
    upload_chunks_to_pinecone("data/chunks.txt")
    print("✅ Done uploading chunks.")
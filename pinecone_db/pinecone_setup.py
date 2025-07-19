# pinecone_setup.py

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from config import Config

# Load environment variables from .env
load_dotenv()

# Load config values
API_KEY = Config.PINECONE_API_KEY
ENVIRONMENT = Config.PINECONE_ENV
INDEX_NAME = Config.PINECONE_INDEX_NAME
DIMENSION = 384  # Match with embedding model output
METRIC = "cosine"

# Initialize Pinecone client
pinecone_client = Pinecone(api_key=API_KEY)

def create_index_if_not_exists(index_name=INDEX_NAME, dimension=DIMENSION, metric=METRIC):
    """
    Creates a Pinecone index if it doesn't already exist.
    """
    existing_indexes = pinecone_client.list_indexes()
    if index_name not in existing_indexes:
        print(f"📦 Creating Pinecone index '{index_name}'...")
        pinecone_client.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud="aws", region=ENVIRONMENT)
        )
        print(f"✅ Index '{index_name}' created successfully.")
    else:
        print(f"ℹ️ Index '{index_name}' already exists. Skipping creation.")

def get_index(index_name=INDEX_NAME):
    """
    Returns a Pinecone index object for querying/upserting.
    """
    return pinecone_client.Index(index_name)

# Example usage
if __name__ == "__main__":
    create_index_if_not_exists()
    index = get_index()
    print(f"🔍 Using index: {INDEX_NAME}")

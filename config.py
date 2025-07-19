import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    # GROQ
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV = os.getenv("PINECONE_ENV")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "wash-assistant")

    # Embedding model (local, via SentenceTransformers)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # Chat model (GROQ)
    CHAT_MODEL = "llama3-70b-8192"

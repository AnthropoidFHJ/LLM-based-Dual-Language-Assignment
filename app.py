from config import Config
from flask import Flask, render_template, request
import requests
import pinecone
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Flask app
app = Flask(__name__)

# Pinecone setup
pc = Pinecone(api_key=Config.PINECONE_API_KEY)

# Ensure index exists
if Config.PINECONE_INDEX_NAME not in pc.list_indexes():
    try:
        pc.create_index(
            name=Config.PINECONE_INDEX_NAME,
            dimension=384,  # must match embedding model
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=Config.PINECONE_ENV),
        )
    except pinecone.exceptions.PineconeApiException as e:
        if "ALREADY_EXISTS" in str(e):
            print(f"Index '{Config.PINECONE_INDEX_NAME}' already exists. Skipping creation.")
        else:
            raise e

pinecone_index = pc.Index(Config.PINECONE_INDEX_NAME)

# Load local embedding model
embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)

# GROQ setup
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {Config.GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# --- Utility functions ---

def is_bangla(text):
    """Detect if text is in Bangla."""
    return any('\u0980' <= char <= '\u09FF' for char in text)

def get_embedding(text):
    """Generate local embedding for text."""
    return embedding_model.encode(text).tolist()

def query_pinecone(query_text):
    """Search Pinecone index using vector similarity."""
    query_vector = get_embedding(query_text)
    result = pinecone_index.query(vector=query_vector, top_k=3, include_metadata=True)
    context = "\n\n".join([match['metadata']['text'] for match in result['matches']])
    return context

def ask_llm(context, question):
    """Query GROQ LLM with contextual question."""
    prompt = f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
    payload = {
        "model": Config.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful WASH Report Assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
    return response.json()["choices"][0]["message"]["content"].strip()

def translate_to_bangla(english_text):
    """Translate English response to Bangla using LLM."""
    prompt_bn = f"Translate this to Bangla: {english_text}"
    payload = {
        "model": Config.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful translator."},
            {"role": "user", "content": prompt_bn}
        ]
    }
    response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
    return response.json()["choices"][0]["message"]["content"].strip()

# --- Flask route ---
@app.route("/", methods=["GET", "POST"])
def home():
    answer = ""
    question = ""
    if request.method == "POST":
        question = request.form["question"]
        context = query_pinecone(question)
        english_answer = ask_llm(context, question)

        if is_bangla(question):
            bangla_translation = translate_to_bangla(english_answer)
            answer = f"English:\n{english_answer}\n\nBangla:\n{bangla_translation}"
        else:
            answer = english_answer

    return render_template("index.html", answer=answer, question=question)

if __name__ == "__main__":
    try:
        app.run(debug=True, port=8085)
    except KeyboardInterrupt:
        print("\n[✋] Server stopped by user.")

from config import Config
from flask import Flask, render_template, request
import requests
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

pc = Pinecone(api_key=Config.PINECONE_API_KEY)
pinecone_index = pc.Index(Config.PINECONE_INDEX_NAME)
embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {Config.GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def is_bangla(text):
    return any('\u0980' <= char <= '\u09FF' for char in text)

def get_embedding(text):
    return embedding_model.encode(text).tolist()

def query_pinecone(query_text):
    query_vector = get_embedding(query_text)
    result = pinecone_index.query(vector=query_vector, top_k=3, include_metadata=True)
    context = "\n\n".join([match['metadata']['text'] for match in result['matches']])
    return context

def ask_llm(context, question):
    prompt = (
    "You are a precise and factual assistant.\n"
    "Answer the question using only the provided context below.\n"
    "Keep responses to 1–2 concise sentences: include key numbers/terms without explaination\n\n"
    "if the context need analysis, analysis it and provide the answer in short as possible.\n\n"
    f"Context:\n{context}\n\n"
    f"Question:\n{question}\n\n"
    "Answer:"
)
    payload = {
        "model": Config.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise WASH Report Assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
    data = response.json()
    if "choices" in data and data["choices"]:
        return data["choices"][0]["message"]["content"].strip()
    else:
        print("GROQ API response (no choices):", data)
        return "No answer returned from LLM (API limitation or quota/rate issue)."

def translate_to_bangla(english_text):
    prompt_bn = (
    "You are a precise translator.\n"
    "Translate the following English text to Bangla.\n"
    "Keep the translation concise and accurate, preserving the original meaning.\n\n"
    "Don't include any additional explanations or filler words.\n\n"
    f"Translate this to Bangla: {english_text}")
    payload = {
        "model": Config.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise translator."},
            {"role": "user", "content": prompt_bn}
        ]
    }
    response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
    return response.json()["choices"][0]["message"]["content"].strip()

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
    app.run(debug=True, port=8085)
import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DATA_PATH = "chroma_data"
DATA_DIR = "data/advisories"

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_DATA_PATH)

def chunk_text_by_words(text, chunk_size=200, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

def init_db():
    client = get_chroma_client()
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(name="advisories", embedding_function=default_ef)
    
    if collection.count() == 0:
        if os.path.exists(DATA_DIR):
            for filename in os.listdir(DATA_DIR):
                if filename.endswith(".txt"):
                    filepath = os.path.join(DATA_DIR, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    chunks = chunk_text_by_words(content, chunk_size=200, overlap=50)
                    for i, chunk in enumerate(chunks):
                        if chunk.strip():
                            collection.add(
                                documents=[chunk],
                                metadatas=[{"source": filename}],
                                ids=[f"{filename}_{i}"]
                            )
    return collection

def retrieve_context(query: str, n_results: int = 6) -> str:
    client = get_chroma_client()
    try:
        collection = client.get_collection(name="advisories")
    except:
        collection = init_db()
        
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    context = ""
    if results['documents']:
        for doc in results['documents'][0]:
            context += f"{doc}\n\n"
            
    return context.strip()

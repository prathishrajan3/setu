import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DATA_PATH = "chroma_data"
DATA_DIR = "data/advisories"

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_DATA_PATH)

def init_db():
    client = get_chroma_client()
    # Using ChromaDB's default embedding function (ONNX based) to fit within 512MB RAM
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(name="advisories", embedding_function=default_ef)
    
    if collection.count() == 0:
        # Load data
        if os.path.exists(DATA_DIR):
            for filename in os.listdir(DATA_DIR):
                if filename.endswith(".txt"):
                    filepath = os.path.join(DATA_DIR, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    # basic chunking by double newline
                    chunks = content.split("\n\n")
                    for i, chunk in enumerate(chunks):
                        if chunk.strip():
                            collection.add(
                                documents=[chunk],
                                metadatas=[{"source": filename}],
                                ids=[f"{filename}_{i}"]
                            )
    return collection

def retrieve_context(query: str, n_results: int = 2) -> str:
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

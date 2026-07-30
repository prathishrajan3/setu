from fastapi import FastAPI, File, UploadFile, Form
from app.gemma_client import query_gemma
from app.router import inject_routing_prompt
from app.rag import retrieve_context, init_db
from app.audio_chunker import chunk_audio_cif_inspired
import os
import shutil

app = FastAPI(title="Setu API")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Setu API is running."}

@app.post("/chat")
async def chat(text: str = Form(None), audio: UploadFile = File(None), image: UploadFile = File(None)):
    if audio:
        # Save temp audio
        temp_audio_path = f"temp_{audio.filename}"
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        # Process audio (simulate CIF-inspired chunking if needed)
        # chunk_paths = chunk_audio_cif_inspired(temp_audio_path)
        
        prompt = "Transcribe and answer the user's question from this audio."
        response = query_gemma(prompt, audio=temp_audio_path)
        
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            
        return {"response": response}
        
    elif text:
        # Text path with RAG and routing
        context = retrieve_context(text)
        
        if context:
            augmented_prompt = f"Context:\n{context}\n\nUser Question:\n{text}\n\nAnswer the user based on the context."
        else:
            augmented_prompt = text
            
        routed_prompt = inject_routing_prompt(augmented_prompt)
        response = query_gemma(routed_prompt)
        
        return {"response": response}
        
    return {"error": "Provide text or audio input."}

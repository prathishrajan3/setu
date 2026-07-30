from fastapi import FastAPI, File, UploadFile, Form
from app.gemma_client import query_gemma, get_whisper
from app.router import inject_routing_prompt, route_dialect
from app.rag import retrieve_context, init_db
from app.audio_chunker import chunk_audio_cif_inspired
from app.tools import AVAILABLE_TOOLS
import os
import shutil
import json
import base64
from typing import Optional

app = FastAPI(title="Setu API")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Setu API is running."}

calculate_subsidy_schema = {
    "type": "function",
    "function": {
        "name": "calculate_subsidy",
        "description": "Calculates the expected subsidy for agricultural machinery based on TN Govt schemes.",
        "parameters": {
            "type": "object",
            "properties": {
                "farmer_type": {
                    "type": "string",
                    "description": "The category of the farmer (e.g., small, marginal, sc/st, women, other)"
                },
                "equipment_cost": {
                    "type": "number",
                    "description": "The total cost of the equipment in Rupees"
                },
                "equipment_type": {
                    "type": "string",
                    "description": "The type of equipment (e.g., tractor, power tiller)"
                }
            },
            "required": ["farmer_type", "equipment_cost", "equipment_type"]
        }
    }
}
TOOLS_LIST = [calculate_subsidy_schema]

def handle_tool_calls(message_dict, messages):
    """Executes requested tools, appends to message history, and returns final natural language response."""
    tool_calls = message_dict.get("tool_calls", [])
    if not tool_calls:
        return message_dict.get("content", "")
        
    # Append the assistant's tool call request to the context
    messages.append(message_dict)
    
    for tc in tool_calls:
        func_name = tc.get("function", {}).get("name")
        args = tc.get("function", {}).get("arguments", {})
        
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except:
                args = {}
                
        if func_name in AVAILABLE_TOOLS:
            try:
                result = AVAILABLE_TOOLS[func_name](**args)
            except Exception as e:
                result = f"Error executing tool: {e}"
        else:
            result = f"Unknown tool: {func_name}"
            
        messages.append({
            "role": "tool",
            "content": str(result),
            "name": func_name
        })
        
    # Final pass: feed full context back into Gemma
    final_message = query_gemma(messages=messages)
    return final_message.get("content", "")

@app.post("/chat")
async def chat(
    text: str = Form(None), 
    audio: UploadFile = File(None), 
    image: UploadFile = File(None),
    language_override: Optional[str] = Form(None)
):
    temp_audio_path = None
    temp_image_path = None
    transcribed_text = ""
    audio_languages = []
    WHISPER_LANG_MAP = {"ta": "tamil", "te": "telugu", "hi": "hindi", "en": "english"}
    
    try:
        if audio:
            temp_audio_path = f"temp_{audio.filename}"
            with open(temp_audio_path, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)
                
            chunk_paths = chunk_audio_cif_inspired(temp_audio_path)
            
            model = get_whisper()
            for chunk_path in chunk_paths:
                try:
                    segments, info = model.transcribe(chunk_path)
                    transcribed_text += " ".join([seg.text for seg in segments]) + " "
                    # Capture language with high confidence
                    if info.language_probability > 0.5 and info.language in WHISPER_LANG_MAP:
                        audio_languages.append(WHISPER_LANG_MAP[info.language])
                except Exception as e:
                    print(f"Error transcribing chunk {chunk_path}: {e}")
                finally:
                    if os.path.exists(chunk_path) and chunk_path != temp_audio_path:
                        os.remove(chunk_path)
                        
            transcribed_text = transcribed_text.strip()
            text = (text or "") + f"\n[User Audio Input]: {transcribed_text}"
            
        if image:
            temp_image_path = f"temp_{image.filename}"
            with open(temp_image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
                
        if not text and not image:
            return {"error": "Provide text, audio, or image input."}
            
        query_to_search = transcribed_text if transcribed_text else (text or "")
        
        # 1. Determine dialect
        if language_override and language_override.lower() != "auto-detect":
            dialect = language_override.lower()
        elif audio_languages:
            # Use most frequent language detected by Whisper
            dialect = max(set(audio_languages), key=audio_languages.count)
        else:
            # Fallback to script-based detection on text
            dialect = route_dialect(query_to_search)
        
        # 2. RAG Translation Optimization
        if dialect not in ["english", "unrecognized"] and query_to_search.strip():
            translate_prompt = f"Translate the following agricultural query to English accurately. Return ONLY the English translation, no other text:\n\n{query_to_search}"
            translate_msg = query_gemma(prompt=translate_prompt)
            english_query = translate_msg.get("content", "").strip()
            search_term = english_query if english_query else query_to_search
        else:
            search_term = query_to_search
            
        # RAG NOTE: Translating queries to English acts as a normalization step since the RAG 
        # knowledge base consists of English TNAU documents. If native-language advisory documents 
        # (Tamil, Telugu, Hindi) were available, skipping this translation step and embedding the 
        # native query directly would improve semantic matching and reduce translation bottlenecks.
        context = retrieve_context(search_term)
        
        augmented_prompt = f"Context:\n{context}\n\nUser Question:\n{text}\n\nAnswer the user based on the context." if context else text
        routed_prompt = inject_routing_prompt(dialect, augmented_prompt)
        
        # 3. Build original messages array for context preservation
        messages = [{"role": "user", "content": routed_prompt}]
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                with open(temp_image_path, "rb") as img_file:
                    messages[0]["images"] = [base64.b64encode(img_file.read()).decode("utf-8")]
            except Exception as e:
                print(f"Image encode error: {e}")
        
        # 4. Initial query
        message = query_gemma(messages=messages, tools=TOOLS_LIST)
        
        # 5. Handle tool calls loop with preserved context
        final_response_text = handle_tool_calls(message, messages)
        
        return {"response": final_response_text}
        
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

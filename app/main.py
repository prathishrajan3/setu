from fastapi import FastAPI, File, UploadFile, Form
from app.gemma_client import query_gemma, get_whisper
from app.router import inject_routing_prompt
from app.rag import retrieve_context, init_db
from app.audio_chunker import chunk_audio_cif_inspired
from app.tools import AVAILABLE_TOOLS
import os
import shutil
import json

app = FastAPI(title="Setu API")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Setu API is running."}

# Define the Ollama tool schema for calculate_subsidy
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

def handle_tool_calls(message_dict):
    """Executes requested tools and returns the natural language response string."""
    tool_calls = message_dict.get("tool_calls", [])
    if not tool_calls:
        return message_dict.get("content", "")
        
    tool_responses = []
    for tc in tool_calls:
        func_name = tc.get("function", {}).get("name")
        args = tc.get("function", {}).get("arguments", {})
        
        # Ollama sometimes returns args as a string, sometimes as a dict
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
            
        tool_responses.append(f"Tool {func_name} returned: {result}")
        
    # Second pass: feed tool results back into Gemma
    # We construct a follow-up prompt for simplicity in this mock
    followup_prompt = "The tool has returned the following data:\n" + "\n".join(tool_responses) + "\n\nPlease provide a final natural language answer to the user."
    final_message = query_gemma(prompt=followup_prompt)
    return final_message.get("content", "")

@app.post("/chat")
async def chat(text: str = Form(None), audio: UploadFile = File(None), image: UploadFile = File(None)):
    temp_audio_path = None
    temp_image_path = None
    transcribed_text = ""
    
    try:
        if audio:
            temp_audio_path = f"temp_{audio.filename}"
            with open(temp_audio_path, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)
                
            # Chunking
            chunk_paths = chunk_audio_cif_inspired(temp_audio_path)
            
            # Process chunks sequentially to get full transcript using local ASR
            model = get_whisper()
            for chunk_path in chunk_paths:
                try:
                    segments, _ = model.transcribe(chunk_path)
                    transcribed_text += " ".join([seg.text for seg in segments]) + " "
                except Exception as e:
                    print(f"Error transcribing chunk {chunk_path}: {e}")
                finally:
                    # Clean up the chunk
                    if os.path.exists(chunk_path) and chunk_path != temp_audio_path:
                        os.remove(chunk_path)
                        
            transcribed_text = transcribed_text.strip()
            # Append transcribed text to the user query
            text = (text or "") + f"\n[User Audio Input]: {transcribed_text}"
            
        if image:
            temp_image_path = f"temp_{image.filename}"
            with open(temp_image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
                
        if not text and not image:
            return {"error": "Provide text, audio, or image input."}
            
        # RAG and routing
        query_to_search = transcribed_text if transcribed_text else (text or "")
        context = retrieve_context(query_to_search)
        
        augmented_prompt = f"Context:\n{context}\n\nUser Question:\n{text}\n\nAnswer the user based on the context." if context else text
        
        # Route through dialect logic
        routed_prompt = inject_routing_prompt(augmented_prompt)
        
        # Initial query (audio_path=None because we already transcribed the chunks above)
        message = query_gemma(prompt=routed_prompt, image_path=temp_image_path, tools=TOOLS_LIST)
        
        # Handle tool calls loop
        final_response_text = handle_tool_calls(message)
        
        return {"response": final_response_text}
        
    finally:
        # Cleanup temp files
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

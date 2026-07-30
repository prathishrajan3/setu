import os
import requests
import base64
import json

MODE = os.environ.get("GEMMA_MODE", "local")

_whisper_model = None
def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        # Using tiny model for hackathon speed constraints, running on CPU
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _whisper_model

def query_gemma(prompt=None, image_path=None, audio_path=None, tools=None, messages=None):
    if messages is None:
        # 1. Handle Audio via local ASR fallback
        if audio_path:
            try:
                model = get_whisper()
                segments, _ = model.transcribe(audio_path)
                transcript = " ".join([segment.text for segment in segments])
                prompt = f"{prompt}\n\n[Transcribed Audio]: {transcript}"
            except Exception as e:
                print(f"ASR Error: {e}")
                prompt = f"{prompt}\n\n[Transcribed Audio: Error transcribing file.]"
                
        # 2. Handle Image encoding
        images_list = []
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as img_file:
                    images_list.append(base64.b64encode(img_file.read()).decode("utf-8"))
            except Exception as e:
                print(f"Image encode error: {e}")

        # Use the /api/chat interface which natively supports tools and multimodal messages
        messages = [{"role": "user", "content": prompt}]
        if images_list:
            messages[0]["images"] = images_list
        
    payload = {
        "stream": False,
        "messages": messages
    }
    if tools:
        payload["tools"] = tools

    if MODE == "local":
        primary_model = os.environ.get("GEMMA_MODEL", "gemma4:12b")
        fallback_model = "gemma4:e4b"
        payload["model"] = primary_model
        
        try:
            resp = requests.post(
                "http://localhost:11434/api/chat",
                json=payload,
                timeout=120 # Local timeout (increased to 120s for model loading)
            )
            resp.raise_for_status()
            return resp.json().get("message", {})
        except requests.exceptions.RequestException as e:
            print(f"Primary model {primary_model} failed, falling back to {fallback_model}. Error: {e}")
            payload["model"] = fallback_model
            try:
                resp = requests.post(
                    "http://localhost:11434/api/chat",
                    json=payload,
                    timeout=120
                )
                resp.raise_for_status()
                return resp.json().get("message", {})
            except requests.exceptions.RequestException as e2:
                return {"role": "assistant", "content": f"Error connecting to local Ollama: {e2}"}
    else:
        api_base = os.environ.get("GEMMA_API_BASE", "")
        api_key = os.environ.get("GEMMA_API_KEY", "")
        payload["model"] = "gemma-4"
        try:
            resp = requests.post(
                api_base,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=60 # Hosted timeout
            )
            resp.raise_for_status()
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]
            return {"role": "assistant", "content": data.get("response", str(data))}
        except requests.exceptions.RequestException as e:
            return {"role": "assistant", "content": f"Error connecting to hosted API: {e}"}

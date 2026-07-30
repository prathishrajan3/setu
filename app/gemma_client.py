import os
import requests

MODE = os.environ.get("GEMMA_MODE", "local")

def query_gemma(prompt, image=None, audio=None):
    if MODE == "local":
        primary_model = os.environ.get("GEMMA_MODEL", "gemma4:12b-unified")
        fallback_model = "gemma4:e4b"
        
        try:
            # talk to local Ollama instance, fully offline
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": primary_model,
                      "prompt": prompt,
                      "stream": False},
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Primary model {primary_model} failed, falling back to {fallback_model}. Error: {e}")
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": fallback_model,
                      "prompt": prompt,
                      "stream": False},
            )
    else:
        # talk to hosted endpoint (Render deployment path)
        api_base = os.environ.get("GEMMA_API_BASE", "")
        api_key = os.environ.get("GEMMA_API_KEY", "")
        resp = requests.post(
            api_base,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"prompt": prompt, "model": "gemma-4"},
        )
    
    if resp.status_code == 200:
        return resp.json().get("response", "") or resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    else:
        return f"Error: {resp.status_code} - {resp.text}"

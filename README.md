# Setu

Offline multimodal farm advisory assistant, powered by Gemma 4.

## Live Demo
[Live Demo](https://your-render-url.onrender.com)
*Note: This is hosted on Render's free tier. The service spins down after 15 minutes of inactivity and may take 30–50 seconds to wake up on the first request.*

## About
Setu was built for the Gemma 4 Hackathon Sprint (GDG VIT Chennai) under the "AI off the Grid" track. It is designed for small and marginal farmers across rural Tamil Nadu who routinely make high-stakes agricultural decisions in fields with zero network connectivity. The project provides an on-device, multimodal assistant that understands code-switched Indic languages and operates fully offline, ensuring farmers have access to critical advisory information exactly when and where they need it most.

## Features
- Ask agricultural questions using text or voice in English, Tamil, Telugu, or Hindi.
- Upload photos of crops or pests for offline visual analysis.
- Calculate Tamil Nadu government subsidies for farm equipment automatically.
- Get answers grounded in local TNAU advisories and government scheme documents.
- Run the entire multimodal pipeline completely offline without internet connectivity.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI (Python) |
| Local LLM | Gemma 4 12b (via Ollama) |
| Vector Store | ChromaDB |
| Speech Recognition | faster-whisper |

## Architecture
The Streamlit frontend captures text, camera photos, or microphone audio. The FastAPI backend processes the inputs: audio is sliced using a silence-aware chunker and transcribed via `faster-whisper`. The backend detects the spoken or written language (Tamil, Telugu, Hindi, English, or code-switched variants) and translates non-English queries to English. It then retrieves relevant context from a local ChromaDB instance loaded with TNAU documents. Finally, it constructs a prompt with language-specific routing instructions and passes it (along with any images) to the Gemma 4 model to either generate a natural language response or trigger a local subsidy calculation tool.

## Running Locally

1. Install [Ollama](https://ollama.com/) and pull the required models:
```bash
ollama pull gemma4:12b
ollama pull gemma4:e4b
```

2. Clone the repository and navigate into it:
```bash
git clone <your-repo-url>
cd setu
```

3. Set up the Python virtual environment and install dependencies:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

4. Start the FastAPI backend (in one terminal):
```bash
export GEMMA_MODE=local
uvicorn app.main:app --port 8000
```

5. Start the Streamlit frontend (in a second terminal):
```bash
export BACKEND_URL="http://localhost:8000"
streamlit run frontend/app.py
```

## Project Structure

```text
setu/
├── app/
│   ├── audio_chunker.py     # Content-aware audio segmentation (RMS silence detection)
│   ├── gemma_client.py      # LLM API abstraction (local Ollama / hosted API)
│   ├── main.py              # FastAPI application and core processing loop
│   ├── rag.py               # ChromaDB initialization and context retrieval
│   ├── router.py            # Script and language heuristic router
│   └── tools.py             # Function-calling definitions (subsidy calculator)
├── data/
│   └── advisories/          # TNAU advisory and government scheme text files
├── frontend/
│   └── app.py               # Streamlit user interface
├── .env.example             # Environment variable templates
├── PRODUCT.md               # Detailed hackathon problem statement and research grounding
├── render.yaml              # Render deployment configuration
└── requirements.txt         # Python dependencies
```

## Key Decisions
- **MoE-inspired language routing:** Instead of relying entirely on raw LLM prompting for code-switched Indic speech, we implemented a heuristic router that forces language-specific system instructions, greatly improving response reliability for Tamil, Telugu, and Hindi inputs.
- **Content-aware audio chunking:** Replaced standard fixed-window audio chunking with a Continuous Integrate-and-Fire (CIF) inspired RMS silence detector. This handles the highly variable speech rates of field recordings much more robustly.
- **Pure Python processing:** Removed the heavy `ffmpeg` dependency for audio chunking by leveraging the native `wave` module, ensuring the codebase deploys smoothly to Render's free tier without requiring a custom Dockerfile.
- **Lightweight embeddings:** Swapped heavy PyTorch-based embedding models (`sentence-transformers`) for ChromaDB's default ONNX embeddings to fit the vector store into Render's strict 512MB RAM limit.
- **Two-tier deployment:** Maintained a strict offline fallback loop using a local Ollama instance for the live demo, while implementing a dynamic API switch to call a hosted Gemma endpoint for public cloud deployment.

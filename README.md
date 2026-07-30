# Setu

Offline multimodal farm advisory assistant, powered by Gemma 4.

Built for the Gemma 4 Hackathon Sprint (GDG VIT Chennai) — Track: AI off the Grid.
**Developed by Team CodeKnight**

## The Problem

Small and marginal farmers across rural India make high stakes decisions every day — identifying a crop disease, choosing the right pesticide, figuring out if a government subsidy covers the treatment. They make these decisions in fields that have no reliable internet connectivity. Every existing AI advisory tool assumes a live cloud API call. The moment signal drops, the tool is useless, precisely when and where the farmer needs it most.

A second problem compounds this: farmer speech in the field is code switched (mixing Tamil, Telugu, or Hindi with English), heavily accented, and recorded in noisy outdoor conditions. Standard speech pipelines trained on clean, monolingual audio degrade badly under these real world conditions.

## What Setu Does

Setu is a fully offline, on device multimodal assistant that runs entirely on local hardware with zero internet dependency during actual use. A farmer can:

* **Show** a photo of a diseased leaf, pest, or soil sample through the camera.
* **Ask** a question by voice or text in English, Tamil, Telugu, or Hindi, including code switched combinations.
* **Receive** an answer grounded in a massive locally stored vector database of Tamil Nadu Agricultural University (TNAU) advisories and government scheme documents, with a built in subsidy calculator triggered automatically when relevant.

Everything — vision understanding, speech transcription, language detection, document retrieval, and reasoning — happens on device.

## How It Works

1. **Input capture:** The premium glassmorphism Streamlit frontend accepts text, camera photos, or audio recordings.
2. **Audio processing:** Audio is split at natural silence boundaries using a CIF inspired RMS chunker (not fixed length windows), then transcribed locally via `faster whisper`. The detected language code from Whisper is used to route the query.
3. **Language detection:** For text inputs, a Unicode script range detector identifies Tamil, Telugu, Hindi, English, or code switched combinations. Language specific system instructions are injected into the prompt.
4. **RAG retrieval:** Non English queries are translated to English via Gemma 4 and matched against a massive local ChromaDB vector store loaded with TNAU advisory documents.
5. **Response generation:** The full context (retrieved documents + user query + any uploaded image) is passed to `google/gemma-4-12b-qat` running locally via LM Studio. If the model determines a subsidy calculation is needed, it triggers the built in tool via function calling.

## Features
* Ask agricultural questions using text or voice in English, Tamil, Telugu, or Hindi.
* Upload photos of crops or pests for offline visual analysis.
* Calculate Tamil Nadu government subsidies for farm equipment automatically.
* Get answers grounded in local TNAU advisories and government scheme documents.
* Premium Apple-style liquid crystal dark mode UI.
* Run the entire multimodal pipeline completely offline without internet connectivity.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI (Python) |
| Local LLM | google/gemma-4-12b-qat (via LM Studio) |
| Vector Store | ChromaDB |
| Speech Recognition | faster whisper |
| Package Manager | uv |

## Running Locally

1. Install [LM Studio](https://lmstudio.ai/) and start the local server. Download the `google/gemma-4-12b-qat` model.
Make sure the LM Studio local server is running on port 1234.

2. Clone the repository and navigate into it:
```bash
git clone <your repo url>
cd setu
```

3. We use the lightning-fast `uv` package manager. Install dependencies and start the virtual environment:
```bash
uv sync
```

4. Start the FastAPI backend (in one terminal):
```bash
uv run uvicorn app.main:app --port 8000
```

5. Start the Streamlit frontend (in a second terminal):
```bash
set BACKEND_URL=http://localhost:8000
uv run streamlit run frontend/app.py
```

## Project Structure

```text
setu/
├── app/
│   ├── audio_chunker.py     # Content aware audio segmentation (RMS silence detection)
│   ├── gemma_client.py      # LLM API abstraction (LM Studio SDK)
│   ├── main.py              # FastAPI application and core processing loop
│   ├── rag.py               # ChromaDB initialization and context retrieval
│   ├── router.py            # Script and language heuristic router
│   └── tools.py             # Function calling definitions (subsidy calculator)
├── data/
│   └── advisories/          # TNAU advisory and government scheme text files
├── frontend/
│   └── app.py               # Streamlit user interface (Apple-style dark mode)
├── pyproject.toml           # uv package manager config
├── .python-version          # Pinned to 3.11 for compatibility
├── PRODUCT.md               # Detailed problem statement and research grounding
└── uv.lock                  # Locked fast dependencies
```

## Key Decisions
* **MoE inspired language routing:** Instead of relying entirely on raw LLM prompting for code switched Indic speech, we implemented a heuristic router that forces language specific system instructions, greatly improving response reliability for Tamil, Telugu, and Hindi inputs.
* **Content aware audio chunking:** Replaced standard fixed window audio chunking with a CIF inspired RMS silence detector. This handles the highly variable speech rates of field recordings much more robustly than naive fixed length slicing.
* **Pure Python audio processing:** Removed the external `ffmpeg` system dependency requirement for audio chunking by using the native `wave` module, keeping the setup straightforward (though PyAV internally bundles libraries for decoding).
* **Lightweight embeddings:** Swapped PyTorch based embedding models (`sentence transformers`) for ChromaDB's default ONNX embeddings, cutting memory usage from several GB to under 200MB for the vector store layer.
* **Zero shot query translation:** Non English queries are translated to English via Gemma 4 before retrieval, since the TNAU advisory documents are in English. This is a pragmatic tradeoff — embedding native language docs directly would be better, but requires a multilingual corpus we did not have time to build.

## Known Limitations
* The audio chunker only parses standard 16 bit PCM WAV files. Non WAV uploads (mp3, m4a) bypass chunking and are transcribed as a single file — the app does not crash, but the CIF inspired segmentation silently does not apply.
* The subsidy calculator covers tractors and power tillers only. Other equipment types return a fallback message directing the user to scheme documents.

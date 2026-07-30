# Setu (சேது)

**Offline multimodal farm advisory assistant, powered by Gemma 4.**
Built for the Gemma 4 Hackathon Sprint (GDG VIT Chennai) — Track: *AI off the Grid*.

Point a camera at a leaf. Ask a question in Tamil. Get an answer — even with
zero internet connection.

See [`PRODUCT.md`](./PRODUCT.md) for the full problem statement, product
rationale, and the research paper this project's speech-handling design is
grounded in.

---

## Why this isn't a vibe-coded wrapper

Our audio-handling design decisions (dialect-aware routing, variable-length
audio chunking) are directly informed by a peer-reviewed 2026 research paper
on multilingual LLM-based ASR, cited in full in `PRODUCT.md` and in our
Kaggle writeup:

> Lin, G., Chen, Z., Fu, Y., Li, K., & Zhang, W-Q. (2026). *Enhancing
> Multilingual LLM-based ASR with Mixture of Experts and Dynamic
> Downsampling.* arXiv:2606.10439.

We did not have the compute (the paper used six A40 GPUs) to reproduce their
trained MoE projector or CIF predictor in a one-day sprint. What we did do
is adopt the *principles* behind both contributions — expert-style routing
for code-switched speech, and content-aware (not fixed-window) audio
chunking — as concrete, citable design constraints rather than defaults. See
`PRODUCT.md` §3 for exactly what we implemented vs. what we scoped as future
work.

---

## Architecture

```
                    ┌─────────────────────────────┐
                    │        Frontend (web)        │
                    │  camera capture + mic input   │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │        Backend (FastAPI)       │
                    │  - dialect/script router       │
                    │    (MoE-routing-inspired)      │
                    │  - content-aware audio chunker │
                    │    (CIF-inspired)               │
                    │  - local RAG (TNAU + scheme     │
                    │    docs, vector store)          │
                    │  - function-calling: subsidy /  │
                    │    cost calculator               │
                    └───────┬───────────────┬─────────┘
                            │               │
              ┌─────────────▼───┐   ┌───────▼─────────────┐
              │  OFFLINE MODE     │   │  DEPLOYED MODE       │
              │  Ollama, local     │   │  Render free tier    │
              │  Gemma 4 12B/E4B   │   │  + hosted Gemma      │
              │  laptop GPU        │   │  endpoint (no local  │
              │  NO INTERNET       │   │  GPU on Render free) │
              └────────────────────┘   └───────────────────────┘
```

Two demo modes exist because Render's free tier has **no GPU and 512MB RAM**
— it physically cannot run a quantized 4–12B model. We're not pretending
otherwise. See "Deployment" below for exactly how each mode works.

---

## Tech stack

- **Model:** Gemma 4, two configurations:
  - `gemma4:12b-unified` (primary — native vision + audio) via Ollama, local only
  - `gemma4:e4b` (fallback / cloud-hosted — lighter, faster) via Ollama locally, or a hosted Gemma endpoint when deployed
- **Backend:** Python, FastAPI
- **Vector store:** ChromaDB (local, file-based — no external service needed)
- **Frontend:** Streamlit (fastest to ship in a one-day sprint) or a minimal HTML/JS page — pick based on team comfort
- **Local inference runtime:** Ollama (GGUF, 4-bit quantized)
- **Deployment:** Render (free tier, backend + frontend only — no model weights shipped to Render)

---

## Repo structure

```
setu/
├── README.md
├── PRODUCT.md
├── requirements.txt
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── router.py            # dialect/script routing (MoE-inspired)
│   ├── audio_chunker.py     # content-aware chunking (CIF-inspired)
│   ├── rag.py                # local vector store + retrieval
│   ├── tools.py              # function-calling: subsidy/cost calculator
│   └── gemma_client.py      # abstraction: local Ollama vs hosted endpoint
├── data/
│   └── advisories/           # sample TNAU + scheme PDFs/text for RAG demo
├── frontend/
│   └── app.py                 # Streamlit UI (camera + mic input)
└── render.yaml                # Render deployment config
```

---

## Local setup (offline mode — this is the mode judges see live)

Requirements: a laptop with a GPU (developed against an RTX 5070 laptop
GPU, ~8GB VRAM).

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull Gemma 4 (primary + fallback)
ollama pull gemma4:12b-unified
ollama pull gemma4:e4b

# 3. Clone and set up the project
git clone <your-repo-url>
cd setu
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Run backend (point it at local Ollama, no internet needed)
export GEMMA_MODE=local
export GEMMA_MODEL=gemma4:12b-unified   # falls back to gemma4:e4b if this errors
uvicorn app.main:app --reload --port 8000

# 5. Run frontend
streamlit run frontend/app.py
```

At this point you can disable wifi entirely and the app keeps working — that's the point.

---

## Deployment (Render free tier)

Render's free web service tier gives you 512MB RAM and no GPU, so **the
model itself cannot run on Render**. What gets deployed is the backend +
frontend logic, RAG layer, and function-calling — and it talks to a hosted
Gemma endpoint instead of a local Ollama instance.

### Steps

1. **Push this repo to GitHub** (public, per the hackathon's public-repo requirement).
2. **Get a hosted Gemma endpoint** — since you don't have paid infra, use a
   free-tier option:
   - Google AI Studio's free tier (Gemma models via the Gemini API), or
   - OpenRouter's free Gemma 4 endpoint
   Either way, you'll get an API key and a base URL.
3. **Set environment variables on Render:**
   - `GEMMA_MODE=hosted`
   - `GEMMA_API_KEY=<your key>`
   - `GEMMA_API_BASE=<endpoint url>`
4. **Create `render.yaml`** in the repo root:

```yaml
services:
  - type: web
    name: setu-backend
    env: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: GEMMA_MODE
        value: hosted
      - key: GEMMA_API_KEY
        sync: false
      - key: GEMMA_API_BASE
        sync: false
```

5. **On Render dashboard:** New → Blueprint → connect your GitHub repo →
   Render reads `render.yaml` and provisions the free web service
   automatically.
6. **Free-tier caveats to be upfront about (and to mention in your writeup, not hide):**
   - The service **spins down after ~15 minutes of inactivity** and takes
     ~30–50 seconds to wake on the next request. If judges try the deployed
     link cold, tell them to expect a short wake-up delay.
   - 512MB RAM means keep the ChromaDB index small (the sample advisory
     set, not a huge corpus) — this is fine for a hackathon demo.
   - Because Render has no GPU, the deployed version calls a hosted Gemma
     endpoint rather than running fully offline. **Offline is only true for
     the local/laptop mode** — say this explicitly on stage so the claim
     stays accurate.

### `app/gemma_client.py` — the mode switch

```python
import os
import requests

MODE = os.environ.get("GEMMA_MODE", "local")

def query_gemma(prompt, image=None, audio=None):
    if MODE == "local":
        # talk to local Ollama instance, fully offline
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": os.environ.get("GEMMA_MODEL", "gemma4:12b-unified"),
                  "prompt": prompt},
        )
    else:
        # talk to hosted endpoint (Render deployment path)
        resp = requests.post(
            os.environ["GEMMA_API_BASE"],
            headers={"Authorization": f"Bearer {os.environ['GEMMA_API_KEY']}"},
            json={"prompt": prompt},
        )
    return resp.json()
```

---

## What to say on stage

> "The version running right now has no internet connection — that's the
> whole point. We also have a public link for you to try later; that one
> talks to a hosted endpoint instead, because Render's free tier has no GPU
> to run the model locally. We're telling you that upfront rather than
> letting you assume both are identical."

Judges respect disclosed tradeoffs far more than a shiny claim that falls
apart under a follow-up question.

---

## Research citation

Lin, G., Chen, Z., Fu, Y., Li, K., & Zhang, W-Q. (2026). *Enhancing
Multilingual LLM-based ASR with Mixture of Experts and Dynamic
Downsampling.* Tsinghua University. arXiv:2606.10439v1 [cs.SD].
Full grounding of how this informed our design: see `PRODUCT.md`.

## License

MIT (or update per your team's preference).

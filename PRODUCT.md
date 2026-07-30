# Setu (சேது) — Offline Multimodal Farm Advisory Assistant

**Built for the Gemma 4 Hackathon Sprint — GDG VIT Chennai**
**Track:** AI off the Grid
**Team:** [Your Team Name]

---

## 1. The Problem

Small and marginal farmers across rural Tamil Nadu routinely make high-stakes
decisions — what disease is on this leaf, which pesticide to use, whether a
government scheme covers the treatment — in fields that have **no reliable
network connectivity**. Existing AI advisory tools assume a live API call to
the cloud. The moment signal drops, the tool is useless — precisely when and
where the farmer needs it most.

A second, less obvious problem compounds this: farmer speech in the field is
**code-switched Tamil-English, accented, and recorded in noisy outdoor
conditions** (wind, machinery, livestock). Off-the-shelf speech pipelines
tuned on clean, monolingual benchmark audio degrade badly under these
real-world conditions.

## 2. The Solution

Setu is an **on-device, fully offline** multimodal assistant that runs
entirely on local hardware — no internet, no cloud API dependency during
actual field use.

A farmer can:
- **Show** a leaf, pest, or soil sample to the camera
- **Ask**, by voice, in Tamil or code-switched Tamil-English
- **Receive** an answer grounded in a locally stored knowledge base of
  Tamil Nadu Agricultural University (TNAU) advisories and government
  scheme documents, with an offline cost/subsidy calculator invoked via
  function calling when relevant

Everything — vision understanding, speech understanding, retrieval, and
reasoning — happens on-device.

## 3. Why This Is Not a Vibe-Coded Wrapper

A one-day sprint doesn't allow for training our own models from scratch. But
it does allow us to make **deliberate, literature-informed design choices**
instead of defaulting to whatever an LLM suggests first. We grounded two
specific architecture decisions in a recent peer-reviewed research paper
rather than guessing:

> **Lin, G., Chen, Z., Fu, Y., Li, K., & Zhang, W-Q. (2026).**
> *Enhancing Multilingual LLM-based ASR with Mixture of Experts and Dynamic
> Downsampling.* Tsinghua University. arXiv:2606.10439v1 [cs.SD].

This paper studies exactly our failure mode: multilingual, accented speech
being fed into an LLM-based ASR pipeline (Whisper encoder + projector + LLM
decoder). Its two contributions directly shaped our design:

### 3a. MoE-Enhanced Projector → informs our multilingual robustness plan
The paper shows that routing acoustic features through **language-specific
expert sub-networks** (Eq. 1 in the paper: `y = Σ gₖ(x)·Eₖ(x)`), rather than
a single shared linear projector, meaningfully improves cross-lingual
transcription accuracy — cutting WER on their multilingual dev set from
23.26% (baseline) to 16.10% with an MoE projector alone.

We do **not** train our own MoE projector in a one-day sprint — that
required six A40 GPUs and a 1,500-hour dataset in the paper. Instead, this
finding directly informs a documented design decision in our pipeline: we
route Tamil-English code-switched audio through **language-hinted prompting
and a lightweight rule-based dialect/script detector** before it reaches
Gemma 4's native audio pathway, approximating the *intent* of expert
routing at a scale feasible for a hackathon. We cite this explicitly in our
writeup as the literature basis for that decision, and flag full MoE-style
routing as a concrete "future work" item — matching what the paper itself
proposes as the direction worth pursuing.

### 3b. CIF-Based Dynamic Downsampling → informs our audio chunking strategy
The paper shows that fixed-rate downsampling (compressing every 4 audio
frames into 1 token, regardless of speech rate) hurts robustness when
speech rate varies — which is exactly the case with farmers speaking under
field stress, at inconsistent pace, sometimes over background noise. Their
Continuous Integrate-and-Fire (CIF) approach instead **adapts the
compression rate to the actual acoustic content**, improving WER on
out-of-domain multilingual test sets (FLEURS: 13.05% → 10.46%; CommonVoice:
19.57% → 13.87%, per Table 1 of the paper).

We apply the *principle* — variable-length, content-aware audio
segmentation instead of fixed-length windows — when we chunk field
recordings before passing them to Gemma 4's audio input, rather than naively
slicing audio into fixed 5-second blocks. This is a heuristic adaptation of
CIF's core idea, not a reimplementation of the trained CIF predictor, and we
state that distinction plainly in the writeup.

**Why this matters for judging:** our Kaggle writeup will show, with
citation, that our speech-handling decisions trace back to a specific,
recent (June 2026) research finding about exactly the failure mode our
users face — not an arbitrary choice.

## 4. Why Gemma 4

| Requirement | Gemma 4 fit |
|---|---|
| Works with no internet | Open weights, runs fully local via Ollama/llama.cpp |
| Understands a leaf photo | Native vision input, all sizes |
| Understands spoken Tamil | Native audio input on E2B / E4B / 12B Unified |
| Fits on a laptop GPU | E4B and 12B Unified quantize to ~4–8GB VRAM |
| Can call a subsidy calculator | Native function-calling support |
| Multilingual (140+ languages incl. Tamil) | Built into training |

**Primary model:** Gemma 4 12B Unified, 4-bit quantized — the only mid-size
variant with native audio *and* vision together, matching our core
multimodal pitch.
**Fallback model:** Gemma 4 E4B — lighter and faster, used if the 12B is
unstable during the live demo.

## 5. Two-Tier Demo Strategy (see README for technical detail)

1. **On-site offline demo** (the one judges actually watch): runs 100% on a
   laptop with zero network connection, proving the "AI off the Grid" claim
   for real, not just in the writeup.
2. **Public deployed demo** (Render, free tier): a lighter, always-on
   version judges can try remotely before/after the event, since a personal
   laptop can't stay reachable after the hackathon ends. This tier
   necessarily calls a hosted Gemma endpoint rather than running the model
   locally, because Render's free tier has no GPU — this tradeoff is
   disclosed openly rather than hidden.

## 6. Judging Rubric Alignment

- **Gemma Integration (30%):** native multimodal (vision + audio) input,
  function calling, RAG — all load-bearing, not decorative.
- **Innovation & Impact (30%):** concrete underserved-user problem, backed
  by a cited research paper for the hardest technical sub-problem
  (multilingual field-audio robustness).
- **Functionality (20%):** the offline demo mode cannot fail on venue wifi,
  unlike cloud-dependent competitors.
- **Presentation (20%):** clear problem → literature grounding → solution
  → live proof narrative.

## 7. Roadmap Beyond the Hackathon

- Replace the heuristic dialect router with an actual trained MoE projector
  (per the cited paper) once compute allows.
- Replace fixed-window audio chunking with a trained CIF predictor.
- Expand the local knowledge base beyond the sample TNAU/scheme documents
  used for the demo.

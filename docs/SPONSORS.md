# Sponsor Stack

The product stays sponsor-agnostic at its core. Targeted HackMIT sponsors are
incorporated only where they add real product value, and code integrations sit
**behind modular provider interfaces** so a sponsor SDK never leaks into core
workflows or UI. A sponsor SDK appears in exactly one place: its implementation
under `apps/api/providers/`.

Target sponsors: **OpenAI, Elastic, Dropbox, Deepgram, Token Company, Voloridge,
Long Lake, Ramp.** (Not pursuing Devin.)

Two kinds of fit:
- **Code seam** — a provider interface with a sponsor implementation.
- **Challenge alignment** — the sponsor's challenge is answered by product
  behavior/framing, no interface needed.

## Code seams (provider interfaces)

| Interface | Default | Sponsor | Role |
|---|---|---|---|
| `LLMProvider` | stub | **OpenAI** | Explain/summarize, tool calling, Broader/Deeper classification, supporting/contradicting analysis, artifact generation |
| `EmbeddingProvider` | stub | **OpenAI** | Embeddings for user/canvas-local content only (not all of OpenAlex) |
| `SearchProvider` | stub | **Elastic** | Hybrid keyword+semantic search over canvas objects, excerpts, notes, artifacts, parsed PDFs; RAG retrieval |
| `FileSourceProvider` | stub | **Dropbox** | Import user research PDFs from Dropbox into the canvas via the upload pipeline |
| `SpeechProvider` | stub | **Deepgram** | Optional voice input to canvas chat and read-aloud of AI summaries |
| `InferenceOptimizationProvider` | passthrough | **Token Company** | Cache, cheaper-model routing, prompt compression around every LLM call |

`ResearchDataProvider` -> **OpenAlex** (scholarly source of truth, not a sponsor).

## Challenge alignment (no interface)

| Sponsor | Challenge | How Paper Atlas answers it |
|---|---|---|
| **Long Lake** | "Convince a non-believer" — AI materially better than a chatbot | AI understands the research graph, turns explanations into persistent objects, proposes the next direction visually, connects claims to papers/excerpts, reorganizes via user-approved actions |
| **Voloridge** | "Signal in the Noise" — extract signal from huge, messy datasets | The dataset is OpenAlex itself (~250M works). Broader/Deeper + foundational/recent ranking pulls high-signal papers out of that noisy corpus: deterministic feature scoring + LLM rerank + loop suppression |
| **Ramp** | "Save Time. Save Money." | The whole product saves research time — no lost tabs, faster discovery, AI summaries with provenance instead of re-reading papers |

## Notes

### OpenAI — primary intelligence layer
Runs through scoped canvas tools, never direct DB access.

### Elastic — hybrid retrieval layer
Indexes only application/user content and cached metadata. OpenAlex stays the
scholarly source of truth; Elastic does not mirror it. Credit: 30-day Cloud trial.

### Dropbox — file source (core fit)
Dropbox's challenge is turning fragmented content into something organized and
actionable — exactly what Paper Atlas does. `FileSourceProvider` imports research
PDFs from Dropbox through the existing upload/parse pipeline; they become
UPLOADED_FILE source entities on the canvas. SDK isolated in
`providers/dropbox_files.py`.

### Deepgram — optional voice layer
Secondary fit. `SpeechProvider` adds voice input to the chat bar (STT) and
read-aloud of AI explanations (TTS). Off the core research path. $200 credits.

### Token Company — LLM cost saving (real, implementable)
Challenge: save as much as possible on the LLM stack. `InferenceOptimizationProvider`
is the choke point every LLM call passes through — implement caching,
cheaper-model routing, prompt compression (their models at thetokencompany.com).
Measuring tokens saved is the challenge deliverable. Impl in
`providers/token_company.py`. $500 prize.

### Voloridge — signal in the noise (dataset = OpenAlex)
The dataset is OpenAlex itself: a huge, noisy scholarly corpus. Our
recommendation/ranking layer IS the signal extraction — surfacing foundational,
deeper, and high-impact papers and suppressing near-duplicates and loops. No new
interface; it rides on the existing OpenAlex `ResearchDataProvider`.

### Ramp / Long Lake — product framing
No integration; the product already embodies both. Emphasize in the demo.

## Principle
Sponsor services are replaceable after the hackathon. A sponsor SDK lives in one
provider implementation and nowhere else.

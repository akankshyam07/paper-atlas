# Sponsor Stack

The product stays sponsor-agnostic at its core. Sponsor technologies plug in
**behind modular provider interfaces** so they can be demonstrated at HackMIT
without distorting the research workflow or tightly coupling the product to any
single vendor. No core workflow — and no UI component — depends directly on a
sponsor SDK.

Provider interfaces live in [`apps/api/providers/`](../apps/api/providers). The
default implementations run the demo with stubs; swap in a sponsor
implementation by setting the relevant env var and registering it.

## Interface ↔ sponsor mapping

| Interface | Default | Sponsor option | Role |
|---|---|---|---|
| `LLMProvider` | stub | **OpenAI** | Explanations, summaries, tool calling, Broader/Deeper classification, supporting/contradicting analysis, artifact generation |
| `EmbeddingProvider` | stub | **OpenAI** | Embeddings for user/canvas-local content only (not all of OpenAlex) |
| `SearchProvider` | stub | **Elastic** | Hybrid keyword+semantic search over canvas objects, excerpts, notes, artifacts, parsed PDFs; metadata filtering; RAG retrieval |
| `ResearchDataProvider` | OpenAlex | **Voloridge** | Scholarly discovery, citation traversal; Voloridge for structured extraction / cross-paper pattern analysis / high-signal ranking |
| `InferenceOptimizationProvider` | passthrough | **Token Company** | Cost/latency reduction, context compression, routing around long documents — sits behind the AI gateway |

## Sponsor notes

### OpenAI — primary intelligence layer
Runs through the application's scoped canvas tools, never with direct DB access.
Powers the agent, explanations, structured tool calling, and recommendation
classification/reranking.

### Elastic — hybrid retrieval layer
Indexes only application/user-relevant content and cached metadata. OpenAlex
remains the external scholarly source of truth; Elastic does not mirror it.

### Voloridge — research/analysis layer
Fits structured extraction across literature, relationship/pattern detection,
evidence-driven workflows, and ranking high-signal sources from large candidate
sets. Integrate only where it strengthens discovery — behind
`ResearchDataProvider`, not as a disconnected feature. Gate on a real
challenge/API being provided.

### Token Company — inference optimization
Behind the AI/model gateway (`InferenceOptimizationProvider`). Keeps the app
decoupled from a single inference provider.

### Devin — development-time agent, NOT a runtime dependency
Use for parallel implementation of isolated components, generating/testing
backend APIs, integration tests, scoped bug fixes, deploy/repo maintenance. The
shipped product must run without Devin.

### Long Lake — challenge alignment (product behavior, no interface)
Demonstrate AI that is materially more useful than a chatbot: it understands the
research graph, turns explanations into persistent objects, visually proposes
the next research direction, connects claims to papers/excerpts, and reorganizes
the workspace through user-approved actions. The demo narrative: fragmented
research across tabs/PDFs/Wikipedia/chatbots becomes one persistent, inspectable
environment.

## Principle

Sponsor-specific services are replaceable. A sponsor SDK appears in exactly one
place — its provider implementation under `apps/api/providers/` — and nowhere
else. This preserves a clean production architecture after the hackathon.

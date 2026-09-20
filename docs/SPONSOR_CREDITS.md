# Sponsor Credits & Access (HackMIT 2026, 9.19–9.20)

Concrete redemption info for sponsors relevant to Paper Atlas. Source: HackMIT
2026 Sponsor Credits sheet. For the architecture mapping, see [SPONSORS.md](./SPONSORS.md).

## Stack-relevant

| Sponsor | Credit | How to get it | Maps to |
|---|---|---|---|
| **OpenAI** | $50 Codex + $50 API per person (up to 320) | OpenAI credit request form | `LLMProvider`, `EmbeddingProvider` |
| **Elastic** | 30-day Elastic Cloud trial | https://www.elastic.co/cloud/cloud-trial-overview/30-days | `SearchProvider` |
| **Meta** | $50 Meta (Llama) Model API credits | account at https://dev.meta.ai/ + intake form | alt `LLMProvider` (fallback) |
| **Cognition / Devin** | $1000 Devin credits per team | Google form (see sheet), then booth | dev-time agent (not runtime) |
| **Voloridge** | AWS CPU/GPU compute for their challenge | talk to Voloridge booth | compute (see note below) |

## Useful, not core

- **Mintlify** — 1 month Pro, code `MINTHACKMIT`. Option for hosting our docs.
- **RunPod** — $15 credit codes at booth. GPU if we ever self-host embeddings.
- **Deepgram** — $200 voice AI credits (https://dpgr.am/hackmit26). Only if we add audio.

## Corrections to earlier assumptions

Two mappings in the first draft of SPONSORS.md were wrong against the actual
credits sheet, and have been fixed there:

1. **Voloridge is compute, not a research data API.** It provides AWS CPU/GPU
   instances for teams on the Voloridge challenge — not a scholarly-data or
   analysis endpoint. So it does **not** back `ResearchDataProvider`. OpenAlex
   remains the sole `ResearchDataProvider`. Voloridge is only relevant if we run
   heavy local processing/ML and want their compute; not required for the MVP.
2. **Token Company is not a HackMIT 2026 sponsor.** No credit or offering exists
   in the sheet. `InferenceOptimizationProvider` stays in the codebase as a
   passthrough interface (useful seam), but has no sponsor implementation.

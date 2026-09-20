# Research Canvas — Agent Instructions

## Mission
Build the MVP described in `docs/PRD.md`.

The product is an AI-native visual research canvas centered on research papers, linked knowledge objects, provenance, graph-aware retrieval, and user-approved AI changes.

## Start Here
Before coding a feature:
1. Read the relevant section of `docs/PRD.md`.
2. Inspect existing code and conventions.
3. State the implementation plan briefly.
4. Implement the smallest coherent vertical slice.
5. Run focused tests, typecheck, and lint.
6. For UI changes, verify the actual interaction in-browser when possible.
7. Do not silently expand scope.

## Architectural Constraints
- Do NOT mirror all OpenAlex data.
- Do NOT fine-tune a model for MVP.
- OpenAlex is the scholarly metadata/discovery source of truth.
- Separate canonical source entities from canvas object instances.
- Preserve provenance for every derived artifact.
- AI gets scoped tools, never raw DB mutation access.
- Autonomous persistent AI changes must be proposals requiring user approval.
- A direct user action such as "Explain selection" counts as approval for that explicit derived object.
- Selected-node context has priority over whole-canvas context.
- "Broader" and "Deeper" must use different directional recommendation logic.
- Suggested nodes are previews until accepted.
- Do not automatically add Wikipedia nodes.
- Avoid heavyweight PDF/web viewers inside every canvas node; mount them on focus/expand.
- Prefer boring, mature libraries over custom infrastructure.

## Product Invariants
- The canvas is a visual graph.
- Every accepted object has stable identity.
- Every edge belongs to a canvas.
- A canonical paper can appear on multiple canvases.
- Derived objects preserve source IDs and source locations.
- Historical chat-message context snapshots are immutable.
- Deleting a canvas citation edge does not change canonical OpenAlex facts.
- Rejecting a recommendation should suppress immediate resurfacing of the same candidate.
- A "Deeper" traversal must not immediately route back to an ancestor or near-duplicate.

## Recommended Stack
Follow the repository if already initialized. Otherwise:
- Frontend: Next.js + React + TypeScript
- Canvas: React Flow or equivalent
- PDF: PDF.js
- Backend: FastAPI
- DB: PostgreSQL + pgvector
- Object storage: S3-compatible
- E2E: Playwright

Do not introduce Redis, queues, microservices, or additional infra until required by an implemented feature.

## OpenAlex Rules
- Use direct ID/DOI fetch whenever possible.
- Batch ID requests where useful.
- Use `select=` to minimize payload.
- Cache only touched works.
- Use keyword search for literal lookup.
- Use semantic search for meaning/long-text discovery.
- Use `referenced_works` for outgoing citations.
- Use `cites:<work_id>` for incoming citations.
- Prefer `content_urls.pdf`, then `best_oa_location`, then user upload.
- Never bypass paywalls.

## AI / Retrieval Rules
Retrieval priority:
1. active selection
2. explicitly selected/pinned objects
3. graph neighbors
4. semantic canvas retrieval
5. OpenAlex discovery only when needed

Do not put the entire canvas or entire PDFs into model context by default.

For AI-created persistent canvas changes:
- generate a proposal
- show the proposed diff/state
- require accept/reject

## Code Quality
- Type all public interfaces.
- Keep domain logic separate from UI.
- Do not bury OpenAlex payload assumptions in components.
- Validate external API payloads.
- Make graph mutations transactional.
- Keep recommendation scoring deterministic before optional LLM reranking.
- Keep LLM output schemas structured and validated.
- Add migrations for schema changes.
- Avoid premature abstractions.

## Tests Required
Every feature should add focused tests.

Must test:
- canonical paper deduplication
- graph create/delete/update
- provenance
- recommendation deduplication
- broader/deeper classification behavior
- loop suppression
- retrieval priority
- AI proposal acceptance/rejection
- PDF excerpt source mapping

For user-visible critical paths, add or update Playwright tests.

## Definition of Done
A feature is not done until:
- acceptance behavior from PRD works
- focused tests pass
- typecheck passes
- lint passes
- migrations are included when needed
- no debug code remains
- error/loading/empty states exist
- UI interaction is verified for frontend work

## Scope Discipline
When the PRD leaves a minor implementation detail open, choose the simplest reliable option and continue.

Do NOT invent major product features. If an implementation choice materially changes:
- data model
- product behavior
- security boundary
- AI permissions
- external provider
document the decision in `docs/decisions/` before proceeding.

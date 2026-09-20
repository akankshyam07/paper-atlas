# Paper Atlas — Outstanding Work

Every gap found by scanning the repo against [PRD.md](./PRD.md), ordered by what
blocks the demo. Status as of the current `main`.

## What already works end to end

- Canvas: create/open/rename, pan/zoom/drag, groups, undo/redo, object navigator,
  minimap, command palette, autosave
- Real OpenAlex search (no key needed) — real authors, venues, citations, OA status
- **Broader / Deeper** with genuinely distinct pools + scoring, loop suppression,
  3 preview nodes, accept/reject, "Show 3 more", auto-fit to new suggestions
- Explain → AI artifact node with provenance, linked by an `EXPLAINS` edge
- Postgres/Supabase persistence: canvases, objects, edges, source-entity dedup
- Sponsor providers implemented: OpenAI, Elastic, Deepgram, Token Company
  (each auto-activates on its credential, falls back to a stub)
- Token Company savings measured and exposed at `GET /inference/stats` (66.7% on
  repeated explains)
- 29 backend tests pass

---

## P0 — Broken right now

All fixed. CI is green.

1. ~~CI fails on every push.~~ The cause was **not** the missing Postgres service
   as first assumed — CI never reached pytest. `pip install` failed on a
   dependency conflict (`supabase 2.10` pinned `httpx<0.28` against our
   `httpx==0.28.1`), then on `realtime` requiring `pydantic>=2.11.7`. Bumped
   supabase and pydantic; added the Postgres service and `alembic upgrade head`
   that the DB-backed tests would have needed next.
2. ~~`test_providers.py` redundant.~~ Deleted.
3. ~~CORS wide open.~~ Restricted to the web origins via `CORS_ORIGINS`, with
   explicit methods/headers and credentials enabled.

## P1 — Needed for the demo to feel real

4. **Add `OPENAI_API_KEY`** to `apps/api/.env`. Everything is wired; without it
   explanations return stub text. ($50 sponsor credits available.)
5. ~~Papers carry no abstract.~~ `POST /objects` now fetches the work on add and
   stores abstract, authors, venue, topics, keywords and PDF url on the object,
   and writes `openalex_works_cache`. The Viewer renders the real abstract, which
   is also the text the user selects to make excerpts.
6. ~~References / Cited by / Related not implemented.~~ Added `GET /citations`
   (out / in / related). The Viewer tabs load them on demand, and the three menu
   actions now produce the same translucent preview nodes as Broader/Deeper —
   references upstream, citing and related work downstream.
7. ~~Dropbox import returns a stub.~~ Dropbox integration removed entirely.
8. **No upload endpoint.** Uploaded PDF bytes live in a browser `Map` for the
   session only (`CanvasShell.tsx:32`), so PDFs vanish on reload. Needs
   `POST /files` + Supabase Storage (`db/storage.py` is still a stub).

## P2 — PRD features not started

9. **PDF viewer.** No `pdfjs-dist` dependency; no page rendering, text layer,
   zoom, or in-PDF search (PRD §10). Blocks real excerpts with page/coordinate
   provenance.
10. **Wikipedia concept linking — entirely missing** (PRD §11). No keyphrase
    extraction, no Wikipedia resolver, no inline concept spans, no preview, no
    "add to canvas".
11. **Canvas chat has no endpoint.** The chat bar reuses `/explain`
    (`CanvasShell.tsx:283`). Needs a real `POST /chat` with message history.
12. **Threads are not persisted.** `chat_threads` / `chat_messages` tables do not
    exist, so thread-as-node and immutable per-turn `context_snapshot` (PRD §17)
    are unimplemented.
13. **AI proposal system missing** (PRD §16). No `ai_proposals` table, no
    `propose_*` tools, no diff preview, no accept/reject for agent-initiated
    mutations. Only direct actions (Explain) create artifacts today.
14. **RAG / retrieval not implemented** (PRD §15). The `chunks` table exists but
    nothing chunks, embeds, or retrieves. No pgvector column yet, no retrieval
    priority order (selection → pinned → neighbors → canvas → OpenAlex).
15. **Elastic is implemented but never called.** `SearchProvider` has no caller —
    nothing indexes canvas objects and `search_canvas` is unused.
16. **Foundational / Recent discovery** (PRD §14) not implemented.
17. **Supporting / Contradicting work** (PRD §13) not implemented.

## P3 — Data model gaps (PRD §6)

18. Missing tables: `users`, `files`, `chat_threads`, `chat_messages`,
    `ai_proposals`. (`groups`, `excerpts`, `notes` are intentionally modelled
    inside `canvas_objects`, which the PRD allows.)
19. **No pgvector column** on `chunks` — extension is enabled on Supabase but
    migration 0002 was never written.
20. **No auth.** `canvases.user_id` is nullable and never set; every canvas is
    effectively public. Supabase Auth is available if needed.
21. **OpenAlex cache is process-local.** `openalex/client.py` uses an in-memory
    dict; the `openalex_works_cache` table is never written.

## P4 — Quality, testing, deployment

22. **No Playwright / E2E tests at all** (PRD §34 requires them for 10 critical
    flows). No `playwright.config.ts`, no `e2e/` directory.
23. **Rejected suggestions are suppressed only in localStorage.** No
    server-side suppression table, so rejections do not survive a different
    browser (PRD §13.5).
24. **Frontend has no tests.**
25. **No deployment.** Nothing is hosted — needs Vercel (web) + a host for
    FastAPI. Supabase already hosts the DB.
26. **Canvas delete is not implemented** (PRD §31 asks for create/open/rename/
    delete).
27. **`POST /canvas` is not in `packages/types`** — backend-only endpoint, the
    contract is out of sync.
28. **Object count / 100-object performance** never tested (PRD §31, §21).
29. **No error monitoring or observability** (PRD §30).

---

## Suggested order

Fix **1–3** (small, and CI is red). Then **4–7**, which is what makes the demo
look real: abstracts on papers unlock the Viewer, text selection, and excerpts,
and citations turn three dead menu items live. **8–9** (upload + PDF.js) unlock
the whole PDF half of the product. Everything in P2 is a genuine feature build;
pick by what the demo narrative needs — for the Long Lake challenge that is #13.

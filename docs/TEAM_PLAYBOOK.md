# Paper Atlas — Team Playbook

How the four of us build, split work, and push without stepping on each other.
Read this before writing code. For the product spec, see [PRD.md](./PRD.md); for
agent working rules, see [../context.md](../context.md).

---

## 1. What we are building (hackathon demo slice)

The PRD is a full product across 8 phases. We are **not** building all of it. We
build one vertical slice that demonstrates the core magic:

> Search OpenAlex → drop a paper on the canvas → right-click → **Broader / Deeper**
> shows 3 preview nodes → accept one into the graph → **Explain** creates a linked
> AI note that preserves provenance.

Everything else (Wikipedia concepts, full agent proposal system, PDF text-layer
selection, undo/redo, full RAG) is stretch. Add it back only if the demo slice is
solid and time remains.

---

## 2. Architecture

Monorepo. Next.js frontend and FastAPI backend, talking over a shared, typed API
contract. Postgres (with pgvector) is the single source of truth.

```
[ Next.js / React Flow ]  --HTTP-->  [ FastAPI ]  --SQL-->  [ Postgres + pgvector ]
        apps/web                       apps/api                     (Docker)
             \                             |
              \___ shared API contract ___/
                    packages/types
```

- **Frontend** renders the canvas and calls the API. Holds no business logic.
- **Backend** owns all domain logic and the database. Split into two lanes:
  - **canvas/data** — the graph truth (canvases, objects, edges, provenance).
  - **intelligence** — OpenAlex, Broader/Deeper recommendations, AI explain.
- **packages/types** is the seam. Both sides code against it. It changes only by
  group agreement.

Boring stack on purpose: Next.js + React Flow + PDF.js, FastAPI + Postgres +
pgvector, S3-compatible storage if we get to uploads. No Redis, no queues, no
microservices until a shipped feature forces it.

---

## 3. Folder structure

```
paper-atlas/
├── context.md                 # agent working rules
├── docs/
│   ├── PRD.md                  # product spec (reference)
│   └── TEAM_PLAYBOOK.md        # this file
├── packages/
│   └── types/
│       └── api.ts              # SHARED API contract — group-locked
├── apps/
│   ├── web/                    # FRONTEND lane
│   │   ├── app/                # Next.js routes/pages
│   │   ├── components/
│   │   │   ├── canvas/         # React Flow board, pan/zoom, edges
│   │   │   ├── nodes/          # paper card, suggestion node, note node
│   │   │   ├── menu/           # right-click Explore/AI menu
│   │   │   └── chat/           # canvas chat bar
│   │   ├── lib/
│   │   │   └── api.ts          # typed fetch client (imports packages/types)
│   │   └── package.json
│   └── api/                    # BACKEND
│       ├── main.py             # FastAPI app, route registration
│       ├── db/
│       │   ├── session.py
│       │   └── migrations/     # schema migrations
│       ├── models/             # SQLAlchemy models (shared by both BE lanes)
│       ├── canvas/             # BACKEND-DATA lane
│       │   ├── routes.py       # POST /canvas, /objects, /edges
│       │   ├── service.py      # CRUD, provenance, transactional mutations
│       │   └── dedup.py        # source-entity deduplication
│       ├── openalex/           # BACKEND-AI lane
│       │   ├── client.py       # OpenAlex API client + cache
│       │   └── mapping.py      # payload → our model
│       ├── intel/              # BACKEND-AI lane
│       │   ├── routes.py       # GET /search, POST /recommend, /explain
│       │   ├── recommend.py    # Broader vs Deeper scorer (distinct logic)
│       │   └── explain.py      # AI explain endpoint
│       ├── providers/         # sponsor seams: OpenAI/Elastic/Dropbox/Deepgram/Token Co
│       ├── integrations/      # Dropbox import routes (FileSourceProvider)
│       ├── speech/            # optional voice routes (SpeechProvider)
│       └── requirements.txt
└── .gitignore
```

**Ownership rule:** you edit files in *your* lane's folders. Cross-lane change =
ask first. `packages/types` and `apps/api/models` are shared — coordinate before
editing.

---

## 4. Who owns what

| Person | Lane | Branch | Folders they edit | Builds |
|---|---|---|---|---|
| FE #1 + FE #2 | Frontend (co-owned, not subdivided) | `frontend` | `apps/web/**` | Canvas, node cards, right-click menu, suggestion nodes + ✓/×, chat bar |
| BE #1 | Backend — data | `backend-data` | `apps/api/canvas/**`, `apps/api/db/**`, `apps/api/models/**` | Schema + migrations, canvas/object/edge CRUD, provenance, dedup |
| BE #2 | Backend — intelligence | `backend-ai` | `apps/api/intel/**`, `apps/api/openalex/**`, `apps/api/providers/**`, `apps/api/integrations/**`, `apps/api/speech/**` | OpenAlex client + cache, Broader/Deeper scorer, AI explain, sponsor providers, Dropbox import, voice |

The two frontend people share one branch and co-own the whole UI — no internal
task split. They pull before every push and commit in small pieces to stay in
sync.

---

## 5. The API contract (build this first)

Before anyone branches, we agree and land `packages/types/api.ts` on `main`.
Four endpoints define the whole demo:

| Endpoint | Owner lane | Purpose |
|---|---|---|
| `GET /search?q=` | backend-ai | OpenAlex keyword search, returns paper previews |
| `POST /objects` | backend-data | Add a paper (or note) to a canvas as an object |
| `POST /edges` | backend-data | Link two objects with a typed edge |
| `POST /recommend` | backend-ai | body `{objectId, mode: "broader"｜"deeper"}` → 3 candidates |
| `POST /explain` | backend-ai | body `{objectId｜text}` → AI note with source IDs |

Frontend codes against these shapes immediately using stub responses; backend
fills them in. If a shape must change, whoever needs the change edits
`packages/types` **and pings the group in the same message** so the other lanes
pull it.

---

## 6. Branches — which to create, who works where

```
main                 always demo-able. PR-only, no direct pushes.
├── frontend         FE #1 + FE #2
├── backend-data     BE #1
└── backend-ai       BE #2
```

**Create them once, off main, after the contract lands:**

```bash
git checkout main && git pull
git checkout -b frontend      && git push -u origin frontend      # FE pair
git checkout main
git checkout -b backend-data  && git push -u origin backend-data  # BE #1
git checkout main
git checkout -b backend-ai    && git push -u origin backend-ai    # BE #2
```

Lane branches are **long-lived** for the hackathon — one per lane, not one per
task. Keep working on your lane branch the whole event.

---

## 7. When to push and merge

**Push your own lane: constantly.** Small commits, push after every working
chunk. The FE pair especially — pull before every push.

```bash
git checkout <your-lane> && git pull      # get your own branch's latest
# ...work, commit small...
git push
```

**Merge to `main`: early and often** — whenever a slice works end to end, not at
the end of the hackathon. A lane that hides for many hours causes integration
hell.

```bash
git checkout <your-lane>
git pull origin main          # pull main INTO your lane, resolve conflicts HERE
git push
gh pr create --base main --head <your-lane> --fill
# one teammate skims, then merge
```

**After any merge to main, everyone re-syncs:**

```bash
git checkout <your-lane>
git pull origin main
git push
```

This keeps all three lanes close to `main`, so drift and conflicts stay tiny.

---

## 8. Rules that save the demo

- `main` must always run. If a merge breaks it, drop everything and fix it.
- Never edit `packages/types` (or `apps/api/models`) silently — it is the seam
  all lanes depend on. Change it, announce it, everyone pulls.
- Merge to `main` on a rhythm (roughly every few hours), not once at the end.
- Stay in your lane's folders. Cross-lane edits get a heads-up first.
- Commit small and often. Big commits hide conflicts until they hurt.

---

## 9. Rough timeline

1. **Hour 0–1 (all together):** agree the demo slice, write `packages/types`,
   scaffold folders, land it on `main`. Create the three lane branches.
2. **Hour 1 onward (parallel):** FE builds against stubs; BE-data brings up
   schema + CRUD; BE-ai brings up OpenAlex search + recommend.
3. **First integration:** search → add paper → see it on canvas. Merge to main.
4. **Second integration:** Broader/Deeper preview nodes + accept/reject.
5. **Third integration:** Explain → linked AI note with provenance.
6. **Polish + demo script:** empty/loading states, seed data, rehearse the run.

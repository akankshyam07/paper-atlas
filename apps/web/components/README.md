# Frontend components

Built from `docs/design/claude design` (Shell A) against `docs/PRD.md`.

- `Home.tsx` — canvas list (2d); `Sidebar.tsx` — left rail (2a)
- `canvas/` — `CanvasShell` (board + top bar + chat bar + panel wiring), `EmptyState` (2n), `actions` (board actions context for nodes)
- `nodes/` — paper (2e), suggestion ✓/× (2h), AI note, note/excerpt/thread/pdf/group
- `menu/` — right-click Explore / AI / Organize (PRD §25)
- `panel/` — docked right panel: Objects navigator (2j), Details viewer + selection menu (2f/2g), Chat (2i)
- `search/` — ⌘K palette: canvas search, OpenAlex search → Add, actions (2b/2k)
- `integrations/` — Dropbox import modal

All backend calls go through `lib/api.ts` (typed against `packages/types`).
Board state persists in localStorage via `lib/store.ts` until the API grows canvas CRUD.

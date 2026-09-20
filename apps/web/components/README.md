# Frontend components (FE pair, `frontend` branch)

Co-owned, not subdivided. Suggested layout:
- `canvas/` — React Flow board, pan/zoom, edges
- `nodes/`  — paper card, suggestion node (✓/×), AI note node
- `menu/`   — right-click Explore/AI menu (Broader, Deeper, Explain)
- `chat/`   — canvas chat bar

All backend calls go through `lib/api.ts` (typed against `packages/types`).

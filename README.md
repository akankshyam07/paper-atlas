# Paper Atlas

AI-native visual research canvas. Search papers, drop them on an infinite board,
explore **Broader / Deeper**, and derive AI notes that keep their provenance.

- Product spec: [docs/PRD.md](docs/PRD.md)
- Team workflow, branches, ownership: [docs/TEAM_PLAYBOOK.md](docs/TEAM_PLAYBOOK.md)
- API contract (shared, group-locked): [packages/types/api.ts](packages/types/api.ts)

## Layout

```
apps/web        Next.js + React Flow frontend    (branch: frontend)
apps/api        FastAPI backend                   (branches: backend-data, backend-ai)
packages/types  shared API contract
```

## Database (backend)

```bash
docker compose up -d db     # Postgres 16 + pgvector on :5432
```

## Run the backend

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
# http://localhost:8000/health -> {"status":"ok"}   /docs -> interactive stubs
pytest -q                    # 7 stub tests pass
```

## Run the frontend

```bash
cd apps/web
npm install
npm run dev                  # http://localhost:3000 ; /api/* proxies to :8000
```

The endpoints return stub data today, so both apps run before any real logic is
written. Each lane replaces its own stubs on its branch. CI (typecheck + build +
pytest) runs on every PR to `main`.

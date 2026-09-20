// Typed fetch client. All backend calls go through here.
// Imports the shared contract so FE and BE cannot drift apart.
import type {
  SearchResponse,
  AddObjectRequest, AddObjectResponse,
  AddEdgeRequest, AddEdgeResponse,
  RecommendRequest, RecommendResponse,
  ExplainRequest, ExplainResponse,
} from "../../../packages/types/api";

const BASE = "/api"; // rewritten to the FastAPI server in next.config.mjs

async function post<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  search: (q: string): Promise<SearchResponse> =>
    fetch(`${BASE}/search?q=${encodeURIComponent(q)}`).then((r) => r.json()),
  addObject: (req: AddObjectRequest): Promise<AddObjectResponse> =>
    post("/objects", req),
  addEdge: (req: AddEdgeRequest): Promise<AddEdgeResponse> =>
    post("/edges", req),
  recommend: (req: RecommendRequest): Promise<RecommendResponse> =>
    post("/recommend", req),
  explain: (req: ExplainRequest): Promise<ExplainResponse> =>
    post("/explain", req),
};

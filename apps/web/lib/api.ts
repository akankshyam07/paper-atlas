// Typed fetch client. All backend calls go through here.
// Imports the shared contract so FE and BE cannot drift apart.
import type {
  SearchResponse,
  AddObjectRequest, AddObjectResponse,
  AddEdgeRequest, AddEdgeResponse,
  RecommendRequest, RecommendResponse,
  ExplainRequest, ExplainResponse,
  CitationDirection, ChatRequest, ChatResponse, StanceRequest,
  SuppressRequest, RecommendResponse as RecResponse, UploadResponse,
  DropboxListResponse, DropboxImportRequest, DropboxImportResponse,
  TranscribeResponse,
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
  citations: (objectId: string, direction: CitationDirection, limit = 25): Promise<SearchResponse> =>
    fetch(`${BASE}/citations?objectId=${encodeURIComponent(objectId)}&direction=${direction}&limit=${limit}`).then((r) => r.json()),
  chat: (req: ChatRequest): Promise<ChatResponse> => post("/chat", req),
  stance: (req: StanceRequest): Promise<RecResponse> => post("/stance", req),
  suppress: (req: SuppressRequest): Promise<unknown> => post("/suppressions", req),
  discover: (q: string, kind: "foundational" | "recent"): Promise<RecResponse> =>
    fetch(`${BASE}/discover?q=${encodeURIComponent(q)}&kind=${kind}`).then((r) => r.json()),
  deleteCanvas: (id: string): Promise<unknown> =>
    fetch(`${BASE}/canvas/${id}`, { method: "DELETE" }).then((r) => r.json()),
  upload: (file: File, canvasId: string, x = 0, y = 0): Promise<UploadResponse> => {
    const fd = new FormData();
    fd.append("file", file); fd.append("canvasId", canvasId);
    fd.append("x", String(x)); fd.append("y", String(y));
    return fetch(`${BASE}/files`, { method: "POST", body: fd }).then((r) => {
      if (!r.ok) throw new Error(`/files failed: ${r.status}`);
      return r.json();
    });
  },
  dropboxList: (path = ""): Promise<DropboxListResponse> =>
    fetch(`${BASE}/integrations/dropbox/files?path=${encodeURIComponent(path)}`).then((r) => r.json()),
  dropboxImport: (req: DropboxImportRequest): Promise<DropboxImportResponse> =>
    post("/integrations/dropbox/import", req),
  transcribe: (audio: Blob): Promise<TranscribeResponse> => {
    const fd = new FormData();
    fd.append("audio", audio);
    return fetch(`${BASE}/speech/transcribe`, { method: "POST", body: fd }).then((r) => r.json());
  },
  synthesize: (text: string): Promise<Blob> =>
    fetch(`${BASE}/speech/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }).then((r) => r.blob()),
};

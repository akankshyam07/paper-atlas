// Shared API contract for Paper Atlas.
// GROUP-LOCKED: change only by group agreement, then everyone pulls.
// Frontend and backend both code against these shapes.

export type ObjectType = "PAPER" | "PDF" | "NOTE" | "EXCERPT" | "AI_SUMMARY" | "GROUP" | "THREAD";
export type EdgeType = "CITES" | "DERIVED_FROM" | "EXPLAINS" | "RELATED_TO";
export type RecommendMode = "broader" | "deeper";

// A paper as returned by OpenAlex search (preview, not yet on canvas).
export interface PaperPreview {
  openalexId: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  citedByCount: number;
  hasPdf: boolean;
}

// A placed object on a canvas.
export interface CanvasObject {
  id: string;
  canvasId: string;
  objectType: ObjectType;
  sourceEntityId: string | null;
  title: string | null;
  content: Record<string, unknown>;
  x: number;
  y: number;
  createdBy: "USER" | "AI";
}

export interface ObjectEdge {
  id: string;
  canvasId: string;
  sourceObjectId: string;
  targetObjectId: string;
  edgeType: EdgeType;
  provenance: "USER" | "SYSTEM" | "AI";
}

// A single recommendation candidate (shown as a translucent preview node).
export interface Recommendation {
  paper: PaperPreview;
  mode: RecommendMode;
  relationshipLabel: string; // e.g. "foundational method", "narrower application"
  reason: string; // one line, why suggested
  score: number;
}

// ---- Endpoints ----

// GET /search?q=...  -> owner: backend-ai
export interface SearchResponse {
  results: PaperPreview[];
}

// POST /objects  -> owner: backend-data
export interface AddObjectRequest {
  canvasId: string;
  objectType: ObjectType;
  openalexId?: string; // when adding a paper
  title?: string;
  content?: Record<string, unknown>;
  x: number;
  y: number;
}
export interface AddObjectResponse {
  object: CanvasObject;
}

// POST /edges  -> owner: backend-data
export interface AddEdgeRequest {
  canvasId: string;
  sourceObjectId: string;
  targetObjectId: string;
  edgeType: EdgeType;
}
export interface AddEdgeResponse {
  edge: ObjectEdge;
}

// POST /recommend  -> owner: backend-ai
// Broader and Deeper MUST use distinct directional logic (see PRD §13).
export interface RecommendRequest {
  objectId: string;
  mode: RecommendMode;
  offset?: number; // for "Show more"
}
export interface RecommendResponse {
  recommendations: Recommendation[]; // default 3
}

// POST /explain  -> owner: backend-ai
// Creates an AI note; must preserve source IDs (provenance, PRD §2.2).
export interface ExplainRequest {
  objectId?: string;
  text?: string;
  canvasId: string;
}
export interface ExplainResponse {
  object: CanvasObject; // the created AI_SUMMARY note
  edge: ObjectEdge; // EXPLAINS edge back to the source
}

// ==== Sponsor-feature endpoints ====

// Dropbox import (FileSourceProvider). PRD §7/§10/§23.
export interface DropboxFile {
  id: string;
  name: string;
  path: string;
}
// GET /integrations/dropbox/files?path=
export interface DropboxListResponse {
  files: DropboxFile[];
}
// POST /integrations/dropbox/import  -> pulls file, runs upload/parse, places object
export interface DropboxImportRequest {
  canvasId: string;
  fileId: string;
  x: number;
  y: number;
}
export interface DropboxImportResponse {
  object: CanvasObject; // the placed PDF/paper object
}

// Speech (SpeechProvider, optional). PRD §17.
// POST /speech/transcribe  (multipart audio) -> text for the chat bar
export interface TranscribeResponse {
  text: string;
}
// POST /speech/synthesize  -> audio for read-aloud of an AI artifact
export interface SynthesizeRequest {
  text: string;
}
// returns audio bytes (audio/mpeg); no JSON body

// GET /citations?objectId=&direction=out|in|related  -> owner: backend-ai
// out = works this paper cites (references); in = works citing it; related =
// OpenAlex related_works. Returns previews; adding to the canvas stays explicit.
export type CitationDirection = "out" | "in" | "related";
// response shape is SearchResponse

// POST /chat -> owner: backend-ai. Context follows the PRD §15 priority:
// selection, then graph neighbours, then the rest of the canvas.
export interface ChatRequest {
  canvasId: string;
  message: string;
  selectedObjectIds?: string[];
}
export interface ChatResponse {
  reply: string;
  contextObjectIds: string[];
}

// POST /stance -> supporting/contradicting work (PRD §13). Returns RecommendResponse.
export interface StanceRequest {
  objectId: string;
  stance: "supporting" | "contradicting";
}

// POST /suppressions -> record a rejected candidate so it is not resurfaced (§13.5)
export interface SuppressRequest {
  canvasId: string;
  mode: RecommendMode;
  openalexId: string;
}

// POST /canvas, DELETE /canvas/{id}
export interface CreateCanvasRequest { title: string }
export interface CreateCanvasResponse { id: string; title: string }

// POST /files (multipart: file, canvasId, x, y) -> { object, url }
export interface UploadResponse { object: CanvasObject; url: string }

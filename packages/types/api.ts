// Shared API contract for Paper Atlas.
// GROUP-LOCKED: change only by group agreement, then everyone pulls.
// Frontend and backend both code against these shapes.

export type ObjectType = "PAPER" | "NOTE" | "EXCERPT" | "AI_SUMMARY";
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

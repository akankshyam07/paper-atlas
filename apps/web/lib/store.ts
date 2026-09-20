"use client";
// Canvas persistence + undo/redo. Board state lives in localStorage keyed per
// canvas; objects/edges created through the API keep their server ids.
// ponytail: localStorage until the backend grows canvas CRUD (PRD §20
// CanvasService); swap `load`/`save` for fetches then, nothing else changes.
import { useCallback, useEffect, useRef, useState } from "react";
import type { Edge, Node, Viewport } from "reactflow";
import type { CanvasObject, EdgeType, PaperPreview, Recommendation } from "@atlas/types";

export type NodeKind = "paper" | "pdf" | "note" | "excerpt" | "ai" | "thread" | "suggestion" | "group";

export type NodeData = {
  object: CanvasObject;
  paper?: PaperPreview;
  // suggestion-only: the candidate + the node it hangs off
  suggestion?: Recommendation & { anchorId: string };
};

export type EdgeData = { edgeType: EdgeType | "THREAD_CONTEXT" | "EXCERPT_OF" | "NOTE_ON"; provenance: "USER" | "SYSTEM" | "AI" };

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  contextIds: string[]; // snapshot of selected node ids at send time (PRD §6 chat_messages.context_snapshot)
  artifactId?: string; // AI object id when the reply was materialised
};

export type CanvasDoc = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  nodes: Node<NodeData>[];
  edges: Edge<EdgeData>[];
  viewport?: Viewport;
  chat: ChatMessage[];
  rejected: string[]; // `${mode}:${openalexId}` suppression list (PRD §8)
};

export type CanvasMeta = Pick<CanvasDoc, "id" | "title" | "createdAt" | "updatedAt"> & { objectCount: number };

const INDEX = "atlas.canvases";
const docKey = (id: string) => `atlas.canvas.${id}`;

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}
function write(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* quota / private mode: board still works in memory */
  }
}

export const uid = () => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : Math.random().toString(36).slice(2));

export function listCanvases(): CanvasMeta[] {
  return read<CanvasMeta[]>(INDEX, []).sort((a, b) => b.updatedAt - a.updatedAt);
}

export function createCanvas(title = "Untitled canvas"): CanvasDoc {
  const now = Date.now();
  const doc: CanvasDoc = { id: uid(), title, createdAt: now, updatedAt: now, nodes: [], edges: [], chat: [], rejected: [] };
  saveCanvas(doc);
  return doc;
}

export function loadCanvas(id: string): CanvasDoc | null {
  return read<CanvasDoc | null>(docKey(id), null);
}

export function saveCanvas(doc: CanvasDoc) {
  write(docKey(doc.id), doc);
  const meta: CanvasMeta = {
    id: doc.id,
    title: doc.title,
    createdAt: doc.createdAt,
    updatedAt: doc.updatedAt,
    objectCount: doc.nodes.filter((n) => n.type !== "suggestion").length,
  };
  write(INDEX, [meta, ...listCanvases().filter((c) => c.id !== doc.id)]);
}

export function renameCanvas(id: string, title: string) {
  const doc = loadCanvas(id);
  if (doc) saveCanvas({ ...doc, title, updatedAt: Date.now() });
}

export function deleteCanvas(id: string) {
  try {
    localStorage.removeItem(docKey(id));
  } catch {
    /* ignore */
  }
  write(INDEX, listCanvases().filter((c) => c.id !== id));
}

export function isSuppressed(doc: CanvasDoc, mode: string, openalexId: string) {
  return doc.rejected.includes(`${mode}:${openalexId}`) || doc.nodes.some((n) => n.type !== "suggestion" && n.data.paper?.openalexId === openalexId);
}

type Updater = (d: CanvasDoc) => CanvasDoc;

/** Loads a canvas, autosaves every change, keeps an undo/redo stack.
 *  `update(fn)` records history; `update(fn, false)` does not (drags in flight, viewport). */
export function useCanvasDoc(id: string) {
  const [doc, setDocState] = useState<CanvasDoc | null | undefined>(undefined); // undefined = loading, null = missing
  const [saved, setSaved] = useState(true);
  const docRef = useRef<CanvasDoc | null>(null);
  const past = useRef<CanvasDoc[]>([]);
  const future = useRef<CanvasDoc[]>([]);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    docRef.current = loadCanvas(id);
    setDocState(docRef.current);
    past.current = [];
    future.current = [];
  }, [id]);

  const commit = useCallback((next: CanvasDoc) => {
    docRef.current = next;
    setDocState(next);
    setSaved(false);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      saveCanvas(next);
      setSaved(true);
    }, 300);
  }, []);

  const update = useCallback(
    (fn: Updater, undoable = true) => {
      const d = docRef.current;
      if (!d) return;
      if (undoable) {
        past.current = [...past.current.slice(-49), d];
        future.current = [];
      }
      commit({ ...fn(d), updatedAt: Date.now() });
    },
    [commit],
  );

  const undo = useCallback(() => {
    const prev = past.current.pop();
    if (!prev || !docRef.current) return;
    future.current.push(docRef.current);
    commit(prev);
  }, [commit]);

  const redo = useCallback(() => {
    const next = future.current.pop();
    if (!next || !docRef.current) return;
    past.current.push(docRef.current);
    commit(next);
  }, [commit]);

  return { doc, saved, update, undo, redo };
}

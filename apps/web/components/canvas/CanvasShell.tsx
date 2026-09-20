"use client";
// Canvas shell (wireframe 2a): left rail · top bar · board with tool palette,
// chat bar and minimap · docked right panel (Objects / Details / Chat).
// Every board mutation goes through `update` (autosave + undo/redo); anything
// that creates a persistent object or edge also hits the API so ids are stable.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  Background, BackgroundVariant, MarkerType, MiniMap, applyEdgeChanges, applyNodeChanges, useReactFlow,
  type Connection, type Edge, type EdgeChange, type Node, type NodeChange, type Viewport,
} from "reactflow";
import "reactflow/dist/style.css";
import type { CanvasObject, PaperPreview, RecommendMode } from "@atlas/types";
import { api } from "../../lib/api";
import { bbox, fanOut, NODE_H, NODE_W } from "../../lib/layout";
import { isSuppressed, uid, useCanvasDoc, type ChatMessage, type EdgeData, type NodeData, type NodeKind } from "../../lib/store";
import { Sidebar } from "../Sidebar";
import { BoardActionsContext, type BoardActions } from "./actions";
import { EmptyState } from "./EmptyState";
import { PaperNode } from "../nodes/PaperNode";
import { SuggestionNode } from "../nodes/SuggestionNode";
import { AiNoteNode } from "../nodes/AiNoteNode";
import { ExcerptNode, GroupNode, NoteNode, PdfNode, ThreadNode } from "../nodes/TextNodes";
import { ContextMenu, type MenuAction } from "../menu/ContextMenu";
import { CommandPalette, type PaletteAction } from "../search/CommandPalette";
import { SidePanel, type PanelTab } from "../panel/SidePanel";
import { Viewer, type Selection, type SelectionAction } from "../panel/Viewer";
import { ChatPanel } from "../panel/ChatPanel";
import { DropboxImport } from "../integrations/DropboxImport";

const nodeTypes = { paper: PaperNode, suggestion: SuggestionNode, ai: AiNoteNode, note: NoteNode, excerpt: ExcerptNode, thread: ThreadNode, pdf: PdfNode, group: GroupNode };

// ponytail: uploaded PDF bytes live in memory for the session only — there is
// no upload endpoint yet. Cards persist; re-upload to read after a reload.
const pdfBlobs = new Map<string, string>();

function mkObject(canvasId: string, objectType: CanvasObject["objectType"], title: string | null, content: Record<string, unknown>, x: number, y: number, createdBy: "USER" | "AI" = "USER"): CanvasObject {
  return { id: uid(), canvasId, objectType, sourceEntityId: null, title, content, x, y, createdBy };
}
function toNode(kind: NodeKind, object: CanvasObject, extra: Partial<NodeData> = {}, style?: Node["style"]): Node<NodeData> {
  return { id: object.id, type: kind, position: { x: object.x, y: object.y }, data: { object, ...extra }, style };
}
function toEdge(id: string, source: string, target: string, edgeType: EdgeData["edgeType"], provenance: EdgeData["provenance"], ghost = false): Edge<EdgeData> {
  return { id, source, target, data: { edgeType, provenance }, className: ghost ? "ghost" : undefined, markerEnd: { type: MarkerType.Arrow, width: 16, height: 16, color: ghost ? "#9ec8f5" : "#c7c7cc" } };
}
const kindOf = (o: CanvasObject): NodeKind => (o.objectType === "AI_SUMMARY" ? "ai" : o.content.origin === "dropbox" || o.content.filename ? "pdf" : (o.objectType.toLowerCase() as NodeKind));

export function CanvasShell({ id }: { id: string }) {
  const { doc, saved, update, undo, redo } = useCanvasDoc(id);
  const flow = useReactFlow();
  const [zoom, setZoom] = useState(1);
  const [tab, setTab] = useState<PanelTab>("Objects");
  const [panelOpen, setPanelOpen] = useState(true);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [palette, setPalette] = useState<{ open: boolean; query?: string }>({ open: false });
  const [menu, setMenu] = useState<{ id: string; x: number; y: number } | null>(null);
  const [dropbox, setDropbox] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const offsets = useRef<Record<string, number>>({}); // "anchor:mode" -> next offset for Show more

  const say = useCallback((m: string) => { setToast(m); setTimeout(() => setToast(null), 2400); }, []);
  const fail = useCallback((what: string) => (e: unknown) => { console.error(e); say(`${what} failed — is the API running?`); }, [say]);

  const nodes = useMemo(() => doc?.nodes ?? [], [doc]);
  const edges = useMemo(() => doc?.edges ?? [], [doc]);
  const selected = useMemo(() => nodes.filter((n) => n.selected && n.type !== "suggestion"), [nodes]);
  const selectedIds = useMemo(() => new Set(selected.map((n) => n.id)), [selected]);
  const byId = useCallback((nid: string) => nodes.find((n) => n.id === nid), [nodes]);
  const detail = detailId ? byId(detailId) : selected.length === 1 ? selected[0] : undefined;

  // ---- viewport / zoom ----
  useEffect(() => {
    if (!doc) return;
    if (doc.viewport) { flow.setViewport(doc.viewport); setZoom(doc.viewport.zoom); }
    else if (doc.nodes.length) setTimeout(() => flow.fitView({ padding: 0.3 }), 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc?.id]);
  const onMoveEnd = useCallback((_: unknown, vp: Viewport) => { setZoom(vp.zoom); update((d) => ({ ...d, viewport: vp }), false); }, [update]);
  const focusNode = useCallback((nid: string) => {
    flow.fitView({ nodes: [{ id: nid }], duration: 400, maxZoom: 1.2, padding: 0.5 });
    update((d) => ({ ...d, nodes: d.nodes.map((n) => ({ ...n, selected: n.id === nid })) }), false);
  }, [flow, update]);
  const centre = useCallback(() => {
    const el = document.querySelector(".board") as HTMLElement | null;
    const r = el?.getBoundingClientRect();
    return flow.screenToFlowPosition({ x: (r?.left ?? 0) + (r?.width ?? 800) / 2 - NODE_W / 2, y: (r?.top ?? 0) + (r?.height ?? 600) / 2 - NODE_H / 2 });
  }, [flow]);

  // ---- React Flow change plumbing ----
  const onNodesChange = useCallback((changes: NodeChange[]) => {
    const undoable = changes.some((c) => c.type === "remove");
    update((d) => {
      const removed = new Set(changes.filter((c) => c.type === "remove").map((c) => (c as { id: string }).id));
      return { ...d, nodes: applyNodeChanges(changes, d.nodes) as Node<NodeData>[], edges: d.edges.filter((e) => !removed.has(e.source) && !removed.has(e.target)) };
    }, undoable);
  }, [update]);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    update((d) => ({ ...d, edges: applyEdgeChanges(changes, d.edges) as Edge<EdgeData>[] }), changes.some((c) => c.type === "remove"));
  }, [update]);
  const onNodeDragStart = useCallback(() => update((d) => d), [update]); // snapshot for undo
  const onConnect = useCallback((c: Connection) => {
    if (!doc || !c.source || !c.target) return;
    const { source, target } = c;
    api.addEdge({ canvasId: doc.id, sourceObjectId: source, targetObjectId: target, edgeType: "RELATED_TO" })
      .then(({ edge }) => update((d) => ({ ...d, edges: [...d.edges, toEdge(edge.id, source, target, "RELATED_TO", "USER")] })))
      .catch(fail("Linking"));
  }, [doc, update, fail]);

  // ---- creating things ----
  const addPaper = useCallback(async (p: PaperPreview, at?: { x: number; y: number }) => {
    if (!doc) return;
    const pos = at ?? centre();
    const { object } = await api.addObject({ canvasId: doc.id, objectType: "PAPER", openalexId: p.openalexId, title: p.title, content: { openalexId: p.openalexId }, x: pos.x, y: pos.y });
    update((d) => ({ ...d, nodes: [...d.nodes, toNode("paper", object, { paper: p })] }));
    return object;
  }, [doc, centre, update]);

  const addLocal = useCallback((kind: NodeKind, object: CanvasObject, extra: Partial<NodeData> = {}, style?: Node["style"]) => {
    update((d) => ({ ...d, nodes: [...d.nodes, toNode(kind, object, extra, style)] }));
  }, [update]);

  const addNote = useCallback(async (text = "", at?: { x: number; y: number }, linkFrom?: string) => {
    if (!doc) return;
    const pos = at ?? centre();
    const { object } = await api.addObject({ canvasId: doc.id, objectType: "NOTE", content: { text }, x: pos.x, y: pos.y });
    let edge: Edge<EdgeData> | null = null;
    if (linkFrom) {
      const { edge: e } = await api.addEdge({ canvasId: doc.id, sourceObjectId: linkFrom, targetObjectId: object.id, edgeType: "DERIVED_FROM" });
      edge = toEdge(e.id, linkFrom, object.id, "NOTE_ON", "USER");
    }
    update((d) => ({ ...d, nodes: [...d.nodes, toNode("note", object)], edges: edge ? [...d.edges, edge] : d.edges }));
    return object;
  }, [doc, centre, update]);

  const addExcerpt = useCallback(async (sel: Selection) => {
    if (!doc) return;
    const src = byId(sel.objectId);
    const [pos] = src ? fanOut(src, 1, "down", nodes) : [centre()];
    const content = { text: sel.text, sourceObjectId: sel.objectId, textStart: sel.start, textEnd: sel.end, normalizedQuote: sel.text.replace(/\s+/g, " ").trim(), createdFromSelection: true };
    const { object } = await api.addObject({ canvasId: doc.id, objectType: "EXCERPT", content, x: pos.x, y: pos.y });
    const { edge } = await api.addEdge({ canvasId: doc.id, sourceObjectId: sel.objectId, targetObjectId: object.id, edgeType: "DERIVED_FROM" });
    update((d) => ({ ...d, nodes: [...d.nodes, toNode("excerpt", object)], edges: [...d.edges, toEdge(edge.id, sel.objectId, object.id, "EXCERPT_OF", "USER")] }));
    return object;
  }, [doc, byId, nodes, centre, update]);

  const explain = useCallback(async (sourceId: string, text?: string, title = "Explanation") => {
    if (!doc) return;
    const src = byId(sourceId);
    const [pos] = src ? fanOut(src, 1, "down", nodes) : [centre()];
    const { object, edge } = await api.explain({ canvasId: doc.id, objectId: sourceId, text: text ?? String(src?.data.object.content.text ?? src?.data.object.title ?? "") });
    const placed = { ...object, title: object.title ?? title, x: pos.x, y: pos.y, content: { ...object.content, prompt: title, sourceObjectIds: [sourceId], createdAt: Date.now() } };
    update((d) => ({ ...d, nodes: [...d.nodes, toNode("ai", placed)], edges: [...d.edges, toEdge(edge.id, sourceId, placed.id, "EXPLAINS", "AI")] }));
    return placed;
  }, [doc, byId, nodes, centre, update]);

  // ---- recommendations (PRD §13/§25) ----
  const recommend = useCallback(async (anchorId: string, mode: RecommendMode, more = false) => {
    if (!doc) return;
    const anchor = byId(anchorId);
    if (!anchor) return;
    const key = `${anchorId}:${mode}`;
    const offset = more ? offsets.current[key] ?? 0 : 0;
    try {
      const { recommendations } = await api.recommend({ objectId: anchorId, mode, offset });
      offsets.current[key] = offset + recommendations.length;
      const fresh = recommendations.filter((r) => !isSuppressed(doc, mode, r.paper.openalexId)).slice(0, 3);
      update((d) => {
        const keep = (n: Node<NodeData>) => !(n.type === "suggestion" && n.data.suggestion?.anchorId === anchorId && n.data.suggestion.mode === mode);
        const base = d.nodes.filter(keep);
        const spots = fanOut(anchor, fresh.length, mode === "broader" ? "left" : "right", base, 190, 130);
        const ghosts = fresh.map((r, i) => toNode("suggestion", mkObject(d.id, "PAPER", r.paper.title, { index: i, openalexId: r.paper.openalexId }, spots[i].x, spots[i].y, "AI"), { suggestion: { ...r, anchorId } }));
        const ghostEdges = ghosts.map((g) => (mode === "broader" ? toEdge(`g-${g.id}`, g.id, anchorId, "RELATED_TO", "AI", true) : toEdge(`g-${g.id}`, anchorId, g.id, "RELATED_TO", "AI", true)));
        const dropped = new Set(d.nodes.filter((n) => !keep(n)).map((n) => n.id));
        return { ...d, nodes: [...base, ...ghosts], edges: [...d.edges.filter((e) => !dropped.has(e.source) && !dropped.has(e.target)), ...ghostEdges] };
      });
      if (fresh.length === 0) say("No new suggestions — everything is already on the canvas or was rejected.");
    } catch (e) {
      fail("Recommend")(e);
    }
  }, [doc, byId, update, say, fail]);

  const acceptSuggestion = useCallback(async (nid: string) => {
    const g = byId(nid);
    const s = g?.data.suggestion;
    if (!doc || !g || !s) return;
    try {
      const { object } = await api.addObject({ canvasId: doc.id, objectType: "PAPER", openalexId: s.paper.openalexId, title: s.paper.title, content: { openalexId: s.paper.openalexId, recommendedBy: s.anchorId, mode: s.mode, reason: s.reason }, x: g.position.x, y: g.position.y });
      const [src, tgt] = s.mode === "broader" ? [object.id, s.anchorId] : [s.anchorId, object.id];
      const { edge } = await api.addEdge({ canvasId: doc.id, sourceObjectId: src, targetObjectId: tgt, edgeType: "RELATED_TO" });
      update((d) => ({
        ...d,
        nodes: [...d.nodes.filter((n) => n.id !== nid), toNode("paper", object, { paper: s.paper })],
        edges: [...d.edges.filter((e) => e.source !== nid && e.target !== nid), { ...toEdge(edge.id, src, tgt, "RELATED_TO", "AI"), label: s.relationshipLabel, labelStyle: { fontSize: 10, fill: "var(--ink-4)" }, labelBgStyle: { fill: "var(--board)" } }],
      }));
    } catch (e) {
      fail("Accept")(e);
    }
  }, [doc, byId, update, fail]);

  const rejectSuggestion = useCallback((nid: string) => {
    const s = byId(nid)?.data.suggestion;
    if (!s) return;
    update((d) => ({ ...d, rejected: [...d.rejected, `${s.mode}:${s.paper.openalexId}`], nodes: d.nodes.filter((n) => n.id !== nid), edges: d.edges.filter((e) => e.source !== nid && e.target !== nid) }));
  }, [byId, update]);

  // ---- organize ----
  const groupSelection = useCallback(() => {
    if (!doc || selected.length < 2) return;
    const box = bbox(selected);
    const g = mkObject(doc.id, "NOTE", "Group", { kind: "group" }, box.x, box.y);
    update((d) => ({
      ...d,
      nodes: [
        toNode("group", g, {}, { width: box.w, height: box.h }),
        ...d.nodes.map((n) => (selectedIds.has(n.id) ? { ...n, parentNode: g.id, extent: "parent" as const, position: { x: n.position.x - box.x, y: n.position.y - box.y }, selected: false } : n)),
      ],
    }));
  }, [doc, selected, selectedIds, update]);

  const removeNodes = useCallback((ids: string[]) => {
    const rm = new Set(ids);
    update((d) => ({ ...d, nodes: d.nodes.filter((n) => !rm.has(n.id) && !(n.parentNode && rm.has(n.parentNode))), edges: d.edges.filter((e) => !rm.has(e.source) && !rm.has(e.target)) }));
  }, [update]);

  const chatAbout = useCallback((nid: string) => {
    update((d) => ({ ...d, nodes: d.nodes.map((n) => ({ ...n, selected: n.id === nid })) }), false);
    setPanelOpen(true);
    setTab("Chat");
  }, [update]);

  const onMenuAction = useCallback(async (nid: string, a: MenuAction) => {
    const n = byId(nid);
    if (!n || !doc) return;
    switch (a) {
      case "broader": case "deeper": return recommend(nid, a);
      case "related": case "references": case "citedBy": return setPalette({ open: true, query: n.data.object.title ?? "" });
      case "explain": return explain(nid, undefined, "Explanation").catch(fail("Explain"));
      case "summarize": return explain(nid, undefined, "Summary").catch(fail("Summarize"));
      case "chat": return chatAbout(nid);
      case "link": {
        const others = selected.filter((s) => s.id !== nid);
        if (!others.length) return say("Select another node first, then Link.");
        for (const o of others) await api.addEdge({ canvasId: doc.id, sourceObjectId: nid, targetObjectId: o.id, edgeType: "RELATED_TO" }).then(({ edge }) => update((d) => ({ ...d, edges: [...d.edges, toEdge(edge.id, nid, o.id, "RELATED_TO", "USER")] }))).catch(fail("Linking"));
        return;
      }
      case "group": return groupSelection();
      case "duplicate": {
        const copy = { ...n.data.object, id: uid(), x: n.position.x + 40, y: n.position.y + 40 };
        return addLocal(n.type as NodeKind, copy, { paper: n.data.paper });
      }
      case "remove": return removeNodes([nid]);
    }
  }, [byId, doc, recommend, explain, chatAbout, selected, groupSelection, addLocal, removeNodes, update, say, fail]);

  // ---- chat ----
  const send = useCallback(async () => {
    const text = draft.trim();
    if (!doc || !text || chatBusy) return;
    const contextIds = selected.map((n) => n.id);
    const userMsg: ChatMessage = { id: uid(), role: "user", text, contextIds };
    update((d) => ({ ...d, chat: [...d.chat, userMsg] }), false);
    setDraft("");
    setChatBusy(true);
    try {
      // ponytail: /explain is the only LLM endpoint in the contract; swap for a
      // chat endpoint when backend-ai adds one. Selected nodes go as context.
      const ctx = selected.map((n) => `${n.data.object.title ?? ""}\n${n.data.object.content.text ?? ""}`.trim()).filter(Boolean).join("\n---\n");
      const { object } = await api.explain({ canvasId: doc.id, objectId: contextIds[0], text: ctx ? `${text}\n\nContext:\n${ctx}` : text });
      update((d) => ({ ...d, chat: [...d.chat, { id: uid(), role: "assistant", text: String(object.content.text ?? ""), contextIds }] }), false);
    } catch (e) {
      fail("Chat")(e);
    } finally {
      setChatBusy(false);
    }
  }, [draft, doc, chatBusy, selected, update, fail]);

  const saveNote = useCallback(async (m: ChatMessage) => {
    if (!doc) return;
    const anchor = m.contextIds.map(byId).find(Boolean);
    const [pos] = anchor ? fanOut(anchor, 1, "down", nodes) : [centre()];
    const object = mkObject(doc.id, "AI_SUMMARY", "From chat", { text: m.text, prompt: "chat", sourceObjectIds: m.contextIds, createdAt: Date.now() }, pos.x, pos.y, "AI");
    update((d) => ({
      ...d,
      nodes: [...d.nodes, toNode("ai", object)],
      edges: [...d.edges, ...m.contextIds.filter(byId).map((cid) => toEdge(uid(), cid, object.id, "DERIVED_FROM", "AI"))],
      chat: d.chat.map((x) => (x.id === m.id ? { ...x, artifactId: object.id } : x)),
    }));
  }, [doc, byId, nodes, centre, update]);

  const saveThread = useCallback(() => {
    if (!doc || !doc.chat.length) return;
    const ctx = [...new Set(doc.chat.flatMap((m) => m.contextIds))].filter(byId);
    const first = doc.chat.find((m) => m.role === "user");
    const anchor = ctx.map(byId).find(Boolean);
    const [pos] = anchor ? fanOut(anchor, 1, "down", nodes) : [centre()];
    const object = mkObject(doc.id, "NOTE", first?.text.slice(0, 80) ?? "Thread", { kind: "thread", messages: doc.chat, messageCount: doc.chat.length, contextCount: ctx.length, artifactCount: doc.chat.filter((m) => m.artifactId).length }, pos.x, pos.y);
    update((d) => ({ ...d, nodes: [...d.nodes, toNode("thread", object)], edges: [...d.edges, ...ctx.map((cid) => toEdge(uid(), cid, object.id, "THREAD_CONTEXT", "USER"))], chat: [] }));
    say("Thread saved as a node");
  }, [doc, byId, nodes, centre, update, say]);

  const readAloud = useCallback((text: string) => {
    api.synthesize(text).then((b) => new Audio(URL.createObjectURL(b)).play()).catch(fail("Read aloud"));
  }, [fail]);

  const toggleMic = useCallback(async () => {
    if (recorder.current) { recorder.current.stop(); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks: Blob[] = [];
      const r = new MediaRecorder(stream);
      r.ondataavailable = (e) => chunks.push(e.data);
      r.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        recorder.current = null;
        setRecording(false);
        try {
          const { text } = await api.transcribe(new Blob(chunks, { type: r.mimeType }));
          setDraft((d) => (d ? `${d} ${text}` : text));
        } catch (e) { fail("Transcribe")(e); }
      };
      r.start();
      recorder.current = r;
      setRecording(true);
    } catch { say("Microphone unavailable"); }
  }, [fail, say]);

  // ---- files ----
  const addFiles = useCallback((files: FileList | File[], at?: { x: number; y: number }) => {
    if (!doc) return;
    const pos = at ?? centre();
    Array.from(files).filter((f) => f.type === "application/pdf" || f.name.endsWith(".pdf")).forEach((f, i) => {
      const object = mkObject(doc.id, "PAPER", f.name.replace(/\.pdf$/i, ""), { filename: f.name, sizeBytes: f.size, origin: "upload" }, pos.x + i * 30, pos.y + i * 30);
      pdfBlobs.set(object.id, URL.createObjectURL(f));
      addLocal("pdf", object);
    });
  }, [doc, centre, addLocal]);

  // ---- selection menu actions (PRD §10) ----
  const onSelectionAction = useCallback(async (a: SelectionAction, sel: Selection) => {
    try {
      switch (a) {
        case "highlight": await addExcerpt(sel); return say("Excerpt captured");
        case "note": { const ex = await addExcerpt(sel); if (ex) await addNote("", { x: ex.x + NODE_W + 40, y: ex.y }, ex.id); return; }
        case "explain": case "summarize": { const ex = await addExcerpt(sel); if (ex) await explain(ex.id, sel.text, a === "explain" ? "Explanation" : "Summary"); return; }
        case "ask": setDraft(sel.text); setTab("Chat"); return;
        case "related": setPalette({ open: true, query: sel.text.slice(0, 120) }); return;
      }
    } catch (e) { fail("Action")(e); }
  }, [addExcerpt, addNote, explain, say, fail]);

  // ---- keyboard ----
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      const typing = (e.target as HTMLElement)?.tagName === "INPUT" || (e.target as HTMLElement)?.tagName === "TEXTAREA";
      if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette({ open: true }); }
      else if (mod && e.key.toLowerCase() === "z" && !typing) { e.preventDefault(); e.shiftKey ? redo() : undo(); }
      else if (mod && e.key.toLowerCase() === "g" && !typing) { e.preventDefault(); groupSelection(); }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [undo, redo, groupSelection]);

  const actions = useMemo<BoardActions>(() => ({
    open: (nid) => { setDetailId(nid); setTab("Details"); setPanelOpen(true); },
    chatAbout,
    menu: (nid, x, y) => setMenu({ id: nid, x, y }),
    accept: acceptSuggestion,
    reject: rejectSuggestion,
    more: (anchorId, mode) => recommend(anchorId, mode, true),
    readAloud,
    editText: (nid, text) => update((d) => ({ ...d, nodes: d.nodes.map((n) => (n.id === nid ? { ...n, data: { ...n.data, object: { ...n.data.object, content: { ...n.data.object.content, text } } } } : n)) })),
  }), [chatAbout, acceptSuggestion, rejectSuggestion, recommend, readAloud, update]);

  const paletteActions = useMemo<PaletteAction[]>(() => [
    { id: "upload", label: "Upload PDF", run: () => fileInput.current?.click() },
    { id: "dropbox", label: "Import from Dropbox", run: () => setDropbox(true) },
    { id: "note", label: "New note", run: () => addNote().catch(fail("Note")) },
    { id: "fit", label: "Fit canvas", run: () => flow.fitView({ padding: 0.2, duration: 300 }) },
  ], [addNote, fail, flow]);

  if (!doc) return <div className="shell"><Sidebar currentId={id} onSearch={() => setPalette({ open: true })} /><div className="main"><div className="empty" style={{ marginTop: 80 }}>{doc === null ? "Canvas not found." : <span className="spinner" style={{ display: "inline-block" }} />}</div></div></div>;

  const real = nodes.filter((n) => n.type !== "suggestion");
  const detailEdges = detail ? edges.filter((e) => e.source === detail.id || e.target === detail.id).map((e) => { const other = byId(e.source === detail.id ? e.target : e.source); return { id: e.id, label: e.data?.edgeType ?? "", title: other?.data.object.title ?? String(other?.data.object.content.text ?? "").slice(0, 40) }; }) : [];

  return (
    <BoardActionsContext.Provider value={actions}>
      <div className="shell">
        <Sidebar currentId={id} onSearch={() => setPalette({ open: true })} />
        <div className="main">
          <header className="topbar">
            <input className="topbar-title" value={doc.title} aria-label="Canvas title" onChange={(e) => update((d) => ({ ...d, title: e.target.value }), false)} />
            <span className="hint">{saved ? "Saved" : "Saving…"}</span>
            <div className="grow" />
            <div className="zoom" aria-label="Zoom">
              <button onClick={() => flow.zoomOut()} aria-label="Zoom out">−</button>
              <button onClick={() => flow.fitView({ padding: 0.2, duration: 300 })} title="Fit canvas">{Math.round(zoom * 100)}%</button>
              <button onClick={() => flow.zoomIn()} aria-label="Zoom in">+</button>
            </div>
            <button className="btn" onClick={() => { navigator.clipboard?.writeText(location.href); say("Link copied"); }}>Share</button>
            <button className="btn" aria-pressed={panelOpen} onClick={() => setPanelOpen(!panelOpen)} title="Toggle panel">▥</button>
          </header>
          <div className="work">
            <div className="board" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files, flow.screenToFlowPosition({ x: e.clientX, y: e.clientY })); }}>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeDragStart={onNodeDragStart}
                onConnect={onConnect}
                onMoveEnd={onMoveEnd}
                onNodeContextMenu={(e, n) => { e.preventDefault(); setMenu({ id: n.id, x: e.clientX, y: e.clientY }); }}
                onNodeDoubleClick={(_, n) => n.type !== "group" && actions.open(n.id)}
                onPaneClick={() => { setMenu(null); setDetailId(null); }}
                deleteKeyCode={["Backspace", "Delete"]}
                multiSelectionKeyCode="Shift"
                selectionOnDrag
                panOnDrag={[1, 2]}
                panOnScroll
                zoomOnDoubleClick={false}
                minZoom={0.2}
                maxZoom={2}
                snapToGrid
                snapGrid={[12, 12]}
                proOptions={{ hideAttribution: true }}
                defaultEdgeOptions={{ type: "default" }}
              >
                <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="var(--dot)" />
                {real.length > 3 && <MiniMap pannable zoomable style={{ width: 150, height: 96 }} nodeColor={(n) => (n.type === "paper" ? "#d2d2d7" : n.type === "ai" ? "#9ec8f5" : "#e8e8ea")} maskColor="rgba(251,251,252,0.7)" />}
              </ReactFlow>
              <div className="tools" role="toolbar" aria-label="Tools">
                <button className="tool" aria-pressed title="Select (drag to marquee, space+drag or middle-click to pan)">↖</button>
                <button className="tool" title="Group selection (⌘G)" onClick={groupSelection}>▭</button>
                <button className="tool" title="New note" onClick={() => addNote().catch(fail("Note"))}>✎</button>
                <button className="tool" title="Upload PDF" onClick={() => fileInput.current?.click()}>⇪</button>
                <button className="tool accent" title="Ask AI" onClick={() => { setPanelOpen(true); setTab("Chat"); }}>✦</button>
              </div>
              {real.length === 0 && <EmptyState onSearch={() => setPalette({ open: true })} onUpload={() => fileInput.current?.click()} onDropbox={() => setDropbox(true)} onDrop={addFiles} />}
              <form className="chatbar" onSubmit={(e) => { e.preventDefault(); setPanelOpen(true); setTab("Chat"); send(); }}>
                <span style={{ color: "var(--accent)" }}>✦</span>
                <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Ask about this canvas…" aria-label="Ask about this canvas" onFocus={() => { setPanelOpen(true); setTab("Chat"); }} />
                {selected.length > 0 && <span className="pill">{selected.length} selected</span>}
                <button type="button" className="mic" aria-pressed={recording} onClick={toggleMic} title="Voice input">🎙</button>
              </form>
            </div>
            {panelOpen && (
              <SidePanel
                tab={tab} onTab={setTab} wide={tab === "Details" && !!detail}
                nodes={nodes} selectedIds={selectedIds} onFocus={focusNode}
                details={detail ? (
                  <Viewer
                    key={detail.id}
                    node={detail}
                    edges={detailEdges}
                    pdfUrl={pdfBlobs.get(detail.id)}
                    onSelectionAction={onSelectionAction}
                    onAction={(a) => (a === "chat" ? chatAbout(detail.id) : onMenuAction(detail.id, a))}
                  />
                ) : null}
                chat={
                  <ChatPanel
                    messages={doc.chat} contextTitles={selected.map((n) => n.data.object.title ?? String(n.data.object.content.text ?? "").slice(0, 40))}
                    busy={chatBusy} draft={draft} onDraft={setDraft} onSend={send} onSaveNote={saveNote} onSaveThread={saveThread} onReadAloud={readAloud} onMic={toggleMic} recording={recording}
                  />
                }
              />
            )}
          </div>
        </div>
      </div>

      <input ref={fileInput} type="file" accept="application/pdf" multiple hidden onChange={(e) => { if (e.target.files) addFiles(e.target.files); e.target.value = ""; }} />
      {menu && <ContextMenu x={menu.x} y={menu.y} kind={(byId(menu.id)?.type ?? "note") as NodeKind} onAction={(a) => onMenuAction(menu.id, a)} onClose={() => setMenu(null)} />}
      {palette.open && (
        <CommandPalette
          key={palette.query ?? ""}
          nodes={nodes} actions={paletteActions} onFocusNode={focusNode}
          onAdd={(p) => addPaper(p).then(() => say(`Added “${p.title.slice(0, 40)}”`)).catch(fail("Add"))}
          onClose={() => setPalette({ open: false })}
          initialQuery={palette.query}
        />
      )}
      {dropbox && <DropboxImport canvasId={doc.id} at={centre()} onImported={(o) => addLocal(kindOf(o), o)} onClose={() => setDropbox(false)} />}
      {toast && <div className="toast" role="status">{toast}</div>}
    </BoardActionsContext.Provider>
  );
}

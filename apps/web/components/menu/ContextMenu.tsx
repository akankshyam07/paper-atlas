"use client";
// Right-click menu on a node (PRD §25, wireframe 2h): Explore / AI / Organize.
import { useEffect, useRef } from "react";
import type { NodeKind } from "../../lib/store";

export type MenuAction =
  | "broader" | "deeper" | "related" | "references" | "citedBy"
  | "supporting" | "contradicting"
  | "explain" | "summarize" | "chat"
  | "link" | "group" | "compress" | "duplicate" | "remove";

const EXPLORE: [MenuAction, string][] = [
  ["broader", "Broader"], ["deeper", "Deeper"], ["related", "Related papers"],
  ["supporting", "Supporting work"], ["contradicting", "Contradicting work"],
  ["references", "References"], ["citedBy", "Cited by"],
];
const AI: [MenuAction, string][] = [["explain", "Explain"], ["summarize", "Summarize"], ["chat", "Chat about this"]];
const ORGANIZE: [MenuAction, string][] = [["link", "Link to selection"], ["group", "Group selection"], ["compress", "Compress into stack"], ["duplicate", "Duplicate"], ["remove", "Remove from canvas"]];

function Section({ label, items, onPick }: { label: string; items: [MenuAction, string][]; onPick: (a: MenuAction) => void }) {
  return (
    <>
      <div className="eyebrow">{label}</div>
      {items.map(([a, l]) => (
        <button key={a} className={`menu-item${a === "remove" ? " danger" : ""}`} onClick={() => onPick(a)}>{l}</button>
      ))}
    </>
  );
}

export function ContextMenu({ x, y, kind, onAction, onClose }: { x: number; y: number; kind: NodeKind; onAction: (a: MenuAction) => void; onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const off = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && onClose();
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("mousedown", off);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", off);
      document.removeEventListener("keydown", esc);
    };
  }, [onClose]);

  const left = Math.min(x, window.innerWidth - 200);
  const top = Math.min(y, window.innerHeight - 380);
  return (
    <div ref={ref} className="ctx popover" role="menu" style={{ left, top }}>
      {kind === "paper" && (
        <>
          <Section onPick={(a) => { onAction(a); onClose(); }} label="Explore" items={EXPLORE} />
          <div className="divider" />
        </>
      )}
      {kind !== "group" && kind !== "suggestion" && (
        <>
          <Section onPick={(a) => { onAction(a); onClose(); }} label="AI" items={AI} />
          <div className="divider" />
        </>
      )}
      <Section onPick={(a) => { onAction(a); onClose(); }} label="Organize" items={ORGANIZE} />
    </div>
  );
}

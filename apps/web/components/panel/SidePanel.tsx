"use client";
// Docked right panel (wireframe 2a/2j): Objects navigator · Details viewer · Chat.
import { useState, type ReactNode } from "react";
import type { Node } from "reactflow";
import type { NodeData, NodeKind } from "../../lib/store";
import { glyph } from "../search/CommandPalette";

export type PanelTab = "Objects" | "Details" | "Chat";

const FILTERS: [string, NodeKind[] | null][] = [
  ["All", null], ["Papers", ["paper", "pdf"]], ["Notes", ["note"]], ["Excerpts", ["excerpt"]], ["Threads", ["thread"]], ["AI", ["ai"]], ["Groups", ["group"]],
];

export function SidePanel({ tab, onTab, wide, details, chat, nodes, selectedIds, onFocus }: {
  tab: PanelTab; onTab: (t: PanelTab) => void; wide: boolean;
  details: ReactNode; chat: ReactNode;
  nodes: Node<NodeData>[]; selectedIds: Set<string>; onFocus: (id: string) => void;
}) {
  return (
    <aside className={`panel${wide ? " wide" : ""}`} aria-label="Panel">
      <div className="tabs" role="tablist">
        {(["Objects", "Details", "Chat"] as PanelTab[]).map((t) => (
          <button key={t} role="tab" className="tab" aria-selected={tab === t} onClick={() => onTab(t)}>{t}</button>
        ))}
      </div>
      {tab === "Objects" && <Navigator nodes={nodes} selectedIds={selectedIds} onFocus={onFocus} />}
      {tab === "Details" && (details ?? <div className="empty">Select an object to see its details.</div>)}
      {tab === "Chat" && chat}
    </aside>
  );
}

function Navigator({ nodes, selectedIds, onFocus }: { nodes: Node<NodeData>[]; selectedIds: Set<string>; onFocus: (id: string) => void }) {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState(0);
  const [sort, setSort] = useState<"recent" | "type" | "title">("recent");
  const real = nodes.filter((n) => n.type !== "suggestion");
  const kinds = FILTERS[filter][1];
  const term = q.trim().toLowerCase();
  const items = real
    .filter((n) => !kinds || kinds.includes(n.type as NodeKind))
    .filter((n) => !term || (n.data.object.title ?? "").toLowerCase().includes(term) || String(n.data.object.content.text ?? "").toLowerCase().includes(term))
    .sort((a, b) => sort === "title" ? (a.data.object.title ?? "").localeCompare(b.data.object.title ?? "") : sort === "type" ? (a.type ?? "").localeCompare(b.type ?? "") : 0);
  if (sort === "recent") items.reverse();
  const count = (k: NodeKind[] | null) => (k ? real.filter((n) => k.includes(n.type as NodeKind)).length : real.length);

  return (
    <>
      <div style={{ padding: "10px 12px 8px" }}>
        <input className="field" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter objects" aria-label="Filter objects" />
      </div>
      <div className="nav-filters">
        {FILTERS.map(([label, k], i) => (count(k) > 0 || i === 0) && (
          <button key={label} className={`chip click${filter === i ? " solid" : ""}`} aria-pressed={filter === i} onClick={() => setFilter(i)}>{label} {count(k)}</button>
        ))}
        <div className="grow" />
        <select className="chip" aria-label="Sort" value={sort} onChange={(e) => setSort(e.target.value as typeof sort)} style={{ border: "1px solid var(--line)" }}>
          <option value="recent">Recent</option><option value="type">Type</option><option value="title">Title</option>
        </select>
      </div>
      <div className="panel-body">
        {items.length === 0 && <div className="empty">Nothing here yet.</div>}
        {items.map((n) => (
          <button key={n.id} className="nav-item" aria-pressed={selectedIds.has(n.id)} onClick={() => onFocus(n.id)}>
            <span className={`glyph${n.type === "ai" ? " accent" : ""}`}>{glyph(n.type)}</span>
            <span className="title">{n.data.object.title || String(n.data.object.content.text ?? "").slice(0, 60) || "Untitled"}</span>
          </button>
        ))}
      </div>
      <div className="panel-foot">Click an item to fly to it</div>
    </>
  );
}

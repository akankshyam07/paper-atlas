"use client";
// Paper card (wireframe 2e): eyebrow, title, authors · year · venue, chips.
// Hover reveals quick actions ⤢ ✦ ⋯ and the edge handles.
import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../../lib/store";
import { useBoardActions } from "../canvas/actions";

export function QuickActions({ id }: { id: string }) {
  const a = useBoardActions();
  return (
    <div className="node-actions nodrag">
      <button title="Open" onClick={() => a.open(id)}>⤢</button>
      <button className="accent" title="Chat about this" onClick={() => a.chatAbout(id)}>✦</button>
      <button title="More" onClick={(e) => a.menu(id, e.clientX, e.clientY)}>⋯</button>
    </div>
  );
}

export const PaperNode = memo(function PaperNode({ id, data }: NodeProps<NodeData>) {
  const p = data.paper;
  const a = useBoardActions();
  return (
    <div className="node paper">
      <QuickActions id={id} />
      <div className="eyebrow">Paper</div>
      <div className="node-title">{data.object.title}</div>
      {p && (
        <div className="node-sub">
          {p.authors.slice(0, 3).join(", ")}
          {p.authors.length > 3 ? " et al." : ""}
          {p.venue ? ` · ${p.venue}` : ""}
        </div>
      )}
      {p && (
        <div className="node-chips">
          {p.year && <span className="chip">{p.year}</span>}
          <span className="chip">{p.citedByCount.toLocaleString()}</span>
          {p.hasPdf && <span className="chip accent">OA · PDF</span>}
        </div>
      )}
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
});

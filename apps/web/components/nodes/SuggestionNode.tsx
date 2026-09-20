"use client";
// Translucent Broader/Deeper ghost (wireframe 2h): dashed border, reason,
// ✓ accepts (persists node + edge), × rejects (suppressed for this canvas).
import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../../lib/store";
import { useBoardActions } from "../canvas/actions";

export const SuggestionNode = memo(function SuggestionNode({ id, data }: NodeProps<NodeData>) {
  const a = useBoardActions();
  const s = data.suggestion!;
  const p = s.paper;
  const idx = (data.object.content.index as number) ?? 0;
  return (
    <div className="node suggestion" title={`${p.authors.join(", ")}${p.venue ? ` · ${p.venue}` : ""} · ${p.citedByCount.toLocaleString()} citations`}>
      <div className="eyebrow accent">
        {s.mode} · {idx + 1} of 3
      </div>
      <div className="node-title">{p.title}</div>
      <div className="node-sub">
        {p.year ?? "—"} · {s.relationshipLabel}
      </div>
      <div className="node-reason">{s.reason}</div>
      <div className="verdict nodrag">
        <button className="yes" title="Accept" onClick={() => a.accept(id)}>✓</button>
        <button className="no" title="Reject" onClick={() => a.reject(id)}>×</button>
        {idx === 2 && (
          <button className="more" onClick={() => a.more(s.anchorId, s.mode)}>Show 3 more</button>
        )}
      </div>
      {s.mode === "broader" ? <Handle type="source" position={Position.Right} /> : <Handle type="target" position={Position.Left} />}
    </div>
  );
});

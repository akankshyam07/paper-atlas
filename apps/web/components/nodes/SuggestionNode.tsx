"use client";
// Translucent Broader/Deeper preview node with accept/reject. FE wires ✓/× to
// api.addObject + api.addEdge (accept) or a reject/suppress call.
import { Handle, Position, type NodeProps } from "reactflow";

export type SuggestionNodeData = {
  title: string;
  relationshipLabel: string;
  reason: string;
  onAccept?: () => void;
  onReject?: () => void;
};

export function SuggestionNode({ data }: NodeProps<SuggestionNodeData>) {
  return (
    <div style={{ border: "1px dashed #999", borderRadius: 8, padding: 8, background: "rgba(255,255,255,0.6)", width: 220 }}>
      <div style={{ fontSize: 10, textTransform: "uppercase", color: "#888" }}>{data.relationshipLabel}</div>
      <strong style={{ fontSize: 13 }}>{data.title}</strong>
      <div style={{ fontSize: 11, color: "#666" }}>{data.reason}</div>
      <div style={{ marginTop: 6, display: "flex", gap: 8 }}>
        <button onClick={data.onAccept}>✓</button>
        <button onClick={data.onReject}>×</button>
      </div>
      <Handle type="target" position={Position.Left} />
    </div>
  );
}

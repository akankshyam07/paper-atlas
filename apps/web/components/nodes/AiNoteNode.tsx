"use client";
// AI explanation/summary node. Created from /explain, keeps EXPLAINS edge to source.
import { Handle, Position, type NodeProps } from "reactflow";

export type AiNoteNodeData = { title: string; text: string };

export function AiNoteNode({ data }: NodeProps<AiNoteNodeData>) {
  return (
    <div style={{ border: "1px solid #b8a", borderRadius: 8, padding: 8, background: "#faf5ff", width: 220 }}>
      <strong style={{ fontSize: 13 }}>{data.title}</strong>
      <div style={{ fontSize: 11, color: "#555" }}>{data.text}</div>
      <Handle type="target" position={Position.Left} />
    </div>
  );
}

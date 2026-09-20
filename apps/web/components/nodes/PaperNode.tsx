"use client";
// Paper card node. FE builds: title, authors, year, venue, cited-by, OA/PDF badge.
import { Handle, Position, type NodeProps } from "reactflow";

export type PaperNodeData = {
  title: string;
  authors?: string[];
  year?: number | null;
  citedByCount?: number;
};

export function PaperNode({ data }: NodeProps<PaperNodeData>) {
  return (
    <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 8, background: "#fff", width: 220 }}>
      <strong style={{ fontSize: 13 }}>{data.title}</strong>
      <div style={{ fontSize: 11, color: "#666" }}>
        {(data.authors ?? []).slice(0, 3).join(", ")} · {data.year ?? "—"}
      </div>
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
}

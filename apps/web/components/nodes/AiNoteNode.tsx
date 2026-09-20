"use client";
// AI explanation/summary node. Created from /explain, keeps an EXPLAINS edge to
// its source (provenance). Speaker button = optional Deepgram read-aloud.
import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../../lib/store";
import { useBoardActions } from "../canvas/actions";
import { QuickActions } from "./PaperNode";

export const AiNoteNode = memo(function AiNoteNode({ id, data }: NodeProps<NodeData>) {
  const a = useBoardActions();
  const text = String(data.object.content.text ?? "");
  return (
    <div className="node ai">
      <QuickActions id={id} />
      <div className="row">
        <div className="eyebrow">AI explanation</div>
        <div className="grow" />
        <button className="nodrag muted" title="Read aloud" onClick={() => a.readAloud(text)}>🔊</button>
      </div>
      <div className="node-title">{data.object.title}</div>
      <div className="node-text">{text}</div>
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
});

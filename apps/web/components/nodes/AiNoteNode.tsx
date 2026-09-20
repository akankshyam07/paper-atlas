"use client";
// AI explanation/summary node. Created from /explain, keeps EXPLAINS edge to source.
// Speaker button = optional Deepgram read-aloud (SpeechProvider).
import { Handle, Position, type NodeProps } from "reactflow";
import { api } from "../../lib/api";

export type AiNoteNodeData = { title: string; text: string };

export function AiNoteNode({ data }: NodeProps<AiNoteNodeData>) {
  async function readAloud() {
    const audio = await api.synthesize(data.text);
    new Audio(URL.createObjectURL(audio)).play();
  }
  return (
    <div style={{ border: "1px solid #b8a", borderRadius: 8, padding: 8, background: "#faf5ff", width: 220 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <strong style={{ fontSize: 13 }}>{data.title}</strong>
        <button title="Read aloud (Deepgram)" onClick={readAloud}>🔊</button>
      </div>
      <div style={{ fontSize: 11, color: "#555" }}>{data.text}</div>
      <Handle type="target" position={Position.Left} />
    </div>
  );
}

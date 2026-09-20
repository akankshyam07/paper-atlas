"use client";
// Right-click menu on a paper node. FE wires each action to lib/api.
// Explore: Broader, Deeper, Related, References, Cited by
// AI: Explain, Summarize, Chat
export type MenuAction = "broader" | "deeper" | "explain";

export function ContextMenu({ onAction }: { onAction: (a: MenuAction) => void }) {
  return (
    <div style={{ position: "absolute", background: "#fff", border: "1px solid #ccc", borderRadius: 6, padding: 4 }}>
      <button onClick={() => onAction("broader")}>Broader</button>
      <button onClick={() => onAction("deeper")}>Deeper</button>
      <button onClick={() => onAction("explain")}>Explain</button>
    </div>
  );
}

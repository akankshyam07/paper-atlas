"use client";
// Canvas chat bar. FE builds: input + message list, uses selected nodes as context.
import { useState } from "react";

export function ChatBar() {
  const [value, setValue] = useState("");
  return (
    <div style={{ position: "absolute", bottom: 16, left: "50%", transform: "translateX(-50%)", width: 480 }}>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask about the canvas…"
        style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ccc" }}
      />
    </div>
  );
}

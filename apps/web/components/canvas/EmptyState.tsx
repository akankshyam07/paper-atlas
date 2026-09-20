"use client";
// Empty canvas / onboarding (wireframe 2n).
import { useState } from "react";

// The first screen stays at the two actions that start a rabbit hole.
export function EmptyState({ onSearch, onUpload, onDrop }: { onSearch: () => void; onUpload: () => void; onDrop: (files: FileList) => void }) {
  const [over, setOver] = useState(false);
  return (
    <div className="empty-canvas">
      <div>
        <h2>Start the rabbit hole</h2>
        <p>Drop a paper, a PDF, or a question. Everything you derive stays on the board, linked to where it came from.</p>
        <div className="actions">
          <button className="btn lg primary" onClick={onSearch}>Search OpenAlex</button>
          <button className="btn lg" onClick={onUpload}>Upload PDF</button>
        </div>
        <div
          className={`drop${over ? " over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setOver(true); }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => { e.preventDefault(); setOver(false); onDrop(e.dataTransfer.files); }}
        >
          Or drop files anywhere on the canvas
        </div>
        <div className="try">Try: “what makes SAE features interpretable?”</div>
      </div>
    </div>
  );
}

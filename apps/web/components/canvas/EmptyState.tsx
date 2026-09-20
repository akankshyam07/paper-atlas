"use client";
// Empty canvas. Actions only — descriptive filler was restating the buttons.
import { useState } from "react";

export function EmptyState({ onSearch, onUpload, onDrop }: { onSearch: () => void; onUpload: () => void; onDrop: (files: FileList) => void }) {
  const [over, setOver] = useState(false);
  return (
    <div
      className={`empty-canvas${over ? " over" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); onDrop(e.dataTransfer.files); }}
    >
      <div className="actions">
        <button className="btn lg primary" onClick={onSearch}>Search papers</button>
        <button className="btn lg" onClick={onUpload}>Upload files</button>
      </div>
    </div>
  );
}

"use client";
// "Import from Dropbox" — lists Dropbox files, imports one onto the canvas.
// Calls the API; never touches the Dropbox SDK (that lives in the backend).
import { useState } from "react";
import { api } from "../../lib/api";
import type { DropboxFile } from "../../../../packages/types/api";

export function DropboxImport({ canvasId }: { canvasId: string }) {
  const [files, setFiles] = useState<DropboxFile[]>([]);

  async function load() {
    setFiles((await api.dropboxList()).files);
  }

  async function importFile(f: DropboxFile) {
    await api.dropboxImport({ canvasId, fileId: f.id, x: 200, y: 200 });
  }

  return (
    <div>
      <button onClick={load}>Import from Dropbox</button>
      <ul>
        {files.map((f) => (
          <li key={f.id}>
            {f.name} <button onClick={() => importFile(f)}>Add</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

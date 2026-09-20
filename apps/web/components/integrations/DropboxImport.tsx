"use client";
// "Import from Dropbox" — lists Dropbox files, imports one onto the canvas.
// Calls the API; never touches the Dropbox SDK (that lives in the backend).
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { CanvasObject, DropboxFile } from "@atlas/types";

export function DropboxImport({ canvasId, at, onImported, onClose }: { canvasId: string; at: { x: number; y: number }; onImported: (o: CanvasObject) => void; onClose: () => void }) {
  const [files, setFiles] = useState<DropboxFile[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api.dropboxList().then((r) => setFiles(r.files)).catch((e) => setError(String(e)));
  }, []);

  async function importFile(f: DropboxFile) {
    setBusy(f.id);
    try {
      const { object } = await api.dropboxImport({ canvasId, fileId: f.id, x: at.x, y: at.y });
      onImported(object);
      onClose();
    } catch (e) {
      setError(String(e));
      setBusy(null);
    }
  }

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal popover" role="dialog" aria-label="Import from Dropbox">
        <div className="modal-head">
          <strong>Import from Dropbox</strong>
          <div className="grow" />
          <button className="muted" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="modal-body">
          {error && <div className="empty">Couldn’t reach Dropbox. {error}</div>}
          {!files && !error && <div className="empty"><span className="spinner" style={{ display: "inline-block" }} /></div>}
          {files?.length === 0 && <div className="empty">No files found.</div>}
          {files?.map((f) => (
            <div key={f.id} className="result">
              <div className="body">
                <div className="title">{f.name}</div>
                <div className="sub">{f.path}</div>
              </div>
              <button className="btn primary sm" disabled={busy !== null} onClick={() => importFile(f)}>{busy === f.id ? "Adding…" : "Add"}</button>
            </div>
          ))}
        </div>
        <div className="palette-foot">Imported PDFs go through the same parse + dedupe path as uploads.</div>
      </div>
    </div>
  );
}

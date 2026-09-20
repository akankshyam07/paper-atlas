"use client";
// Full document view: centred over a blurred, dimmed board, the way a normal
// file viewer behaves. Escape or a backdrop click closes it.
import { useEffect } from "react";
import type { Node } from "reactflow";
import type { NodeData } from "../../lib/store";

export function Lightbox({ node, pdfUrl, onClose }: {
  node: Node<NodeData>;
  pdfUrl?: string;
  onClose: () => void;
}) {
  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, [onClose]);

  const o = node.data.object;
  const c = o.content as { abstract?: string; text?: string; url?: string };
  const body = String(c.abstract ?? c.text ?? "");
  const web = c.url;

  return (
    <div className="lightbox" onMouseDown={onClose} role="dialog" aria-modal="true" aria-label={o.title ?? "Document"}>
      <div className="lightbox-panel" onMouseDown={(e) => e.stopPropagation()}>
        <div className="lightbox-head">
          <div className="lightbox-title">{o.title}</div>
          <button className="btn" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="lightbox-body">
          {pdfUrl ? <iframe src={pdfUrl} title={o.title ?? "PDF"} />
            : web ? <iframe src={web} title={o.title ?? "Page"} />
            : <div className="reading">{body.split(/\n{2,}/).map((para, i) => <p key={i}>{para}</p>)}</div>}
        </div>
      </div>
    </div>
  );
}

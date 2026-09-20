"use client";
// A paper on the board IS the document: the rendered page, readable at 100%
// zoom, not a metadata card. Books open as a two-page spread that flips.
import { memo, useState } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../../lib/store";
import { useBoardActions } from "../canvas/actions";

export function QuickActions({ id }: { id: string }) {
  const a = useBoardActions();
  return (
    <div className="node-actions nodrag">
      <button title="Open" onClick={() => a.open(id)}>⤢</button>
      <button className="accent" title="Chat about this" onClick={() => a.chatAbout(id)}>✦</button>
      <button title="More" onClick={(e) => a.menu(id, e.clientX, e.clientY)}>⋯</button>
    </div>
  );
}

// Publishers block cross-origin framing, so PDFs render through our own origin.
export const viaProxy = (url?: string) =>
  !url ? undefined : url.startsWith("/") ? url : `/api/proxy/pdf?url=${encodeURIComponent(url)}`;

function Pager({ page, pages, onPrev, onNext, spread }: {
  page: number; pages?: number; onPrev: () => void; onNext: () => void; spread?: boolean;
}) {
  return (
    <div className="pager nodrag" role="group" aria-label="Page navigation">
      <button onClick={onPrev} disabled={page <= 1} aria-label="Previous page">‹</button>
      <span className="pager-count">
        {spread ? `${page}–${page + 1}` : page}{pages ? ` / ${pages}` : ""}
      </span>
      <button onClick={onNext} disabled={!!pages && page >= pages} aria-label="Next page">›</button>
    </div>
  );
}

export const PaperNode = memo(function PaperNode({ id, data }: NodeProps<NodeData>) {
  const p = data.paper;
  const c = data.object.content as {
    pdfUrl?: string; abstract?: string; year?: number; venue?: string;
    authors?: string[]; type?: string; pageCount?: number;
  };
  const src = viaProxy(c.pdfUrl);
  // Books read as a spread; papers are a single column.
  const isBook = (c.type ?? "").includes("book");
  const [page, setPage] = useState(1);
  const [flip, setFlip] = useState<"none" | "fwd" | "back">("none");
  const step = isBook ? 2 : 1;

  const turn = (dir: 1 | -1) => {
    setFlip(dir === 1 ? "fwd" : "back");
    setPage((n) => Math.max(1, n + dir * step));
    window.setTimeout(() => setFlip("none"), 420);
  };

  const meta = [
    (c.authors ?? p?.authors ?? []).slice(0, 3).join(", "),
    String(c.year ?? p?.year ?? ""),
    c.venue ?? p?.venue ?? "",
  ].filter(Boolean).join(" · ");

  return (
    <div className={`node sheet${isBook ? " book" : ""}`} title="Right-click for Broader, Deeper and more · double-click to open">
      <QuickActions id={id} />
      <div className={`sheet-stage${isBook ? " spread" : ""} flip-${flip}`}>
        {src ? (
          isBook ? (
            <>
              <div className="leaf left"><iframe key={`l${page}`} src={`${src}#page=${page}&view=Fit&toolbar=0&navpanes=0&scrollbar=0`} title={`${data.object.title} page ${page}`} /></div>
              <div className="leaf right"><iframe key={`r${page}`} src={`${src}#page=${page + 1}&view=Fit&toolbar=0&navpanes=0&scrollbar=0`} title={`${data.object.title} page ${page + 1}`} /></div>
            </>
          ) : (
            <div className="leaf"><iframe key={page} src={`${src}#page=${page}&view=Fit&toolbar=0&navpanes=0&scrollbar=0`} title={data.object.title ?? "Paper"} /></div>
          )
        ) : (
          // No open-access PDF: typeset the abstract so the node still reads as
          // a page rather than an empty frame.
          <div className="leaf">
            <div className="sheet-fallback">
              <h4>{data.object.title}</h4>
              {meta && <div className="sheet-meta">{meta}</div>}
              <p>{c.abstract ?? "No abstract available for this work."}</p>
            </div>
          </div>
        )}
      </div>
      <div className="sheet-foot">
        <div className="sheet-title" title={data.object.title ?? ""}>{data.object.title}</div>
        {meta && <div className="sheet-sub">{meta}</div>}
      </div>
      {src && <Pager page={page} pages={c.pageCount} spread={isBook} onPrev={() => turn(-1)} onNext={() => turn(1)} />}
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
});

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

// Each pane gets its own document instance. Two iframes pointing at one url
// that differ only by #page can share the loaded document, which is why a
// spread showed the same page twice.
const pageSrc = (src: string, page: number, fit: "Fit" | "FitH") =>
  `${src}${src.includes("?") ? "&" : "?"}pane=${page}#page=${page}&view=${fit}&toolbar=0&navpanes=0&scrollbar=0`;

export const PaperNode = memo(function PaperNode({ id, data }: NodeProps<NodeData>) {
  const p = data.paper;
  const c = data.object.content as {
    pdfUrl?: string; abstract?: string; year?: number; venue?: string;
    authors?: string[]; type?: string; pageCount?: number;
  };
  const src = viaProxy(c.pdfUrl);
  const isBook = (c.type ?? "").includes("book");
  const [page, setPage] = useState(1);
  const [flip, setFlip] = useState<"none" | "fwd" | "back">("none");
  // Reading mode hands the document its own scrolling and text selection. Off
  // by default so the node still drags and right-clicks like a card.
  const [reading, setReading] = useState(false);
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
    <div className={`node sheet${isBook ? " book" : ""}${reading ? " reading" : ""}`}
      title={reading ? "Reading — scroll the document" : "Right-click for Broader, Deeper and more"}>
      <QuickActions id={id} />
      <div className={`sheet-stage${isBook ? " spread" : ""} flip-${flip}`}>
        {src ? (
          isBook ? (
            <>
              <div className="leaf left"><iframe key={`l${page}`} src={pageSrc(src, page, "Fit")} title={`${data.object.title} page ${page}`} /></div>
              <div className="leaf right"><iframe key={`r${page}`} src={pageSrc(src, page + 1, "Fit")} title={`${data.object.title} page ${page + 1}`} /></div>
            </>
          ) : (
            <div className="leaf">
              {/* In reading mode the whole document loads so it scrolls; the
                  card view pins a single fitted page. */}
              <iframe
                key={reading ? "read" : `page-${page}`}
                src={reading ? `${src}#toolbar=0&navpanes=0` : pageSrc(src, page, "Fit")}
                title={data.object.title ?? "Paper"}
              />
            </div>
          )
        ) : (
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
      {src && (
        <div className="pager nodrag" role="group" aria-label="Pages">
          {!reading && (
            <>
              <button onClick={() => turn(-1)} disabled={page <= 1} aria-label="Previous page">‹</button>
              <span className="pager-count">
                {isBook ? `${page}–${page + 1}` : page}{c.pageCount ? ` / ${c.pageCount}` : ""}
              </span>
              <button onClick={() => turn(1)} disabled={!!c.pageCount && page >= c.pageCount} aria-label="Next page">›</button>
            </>
          )}
          {!isBook && (
            <button className="pager-mode" aria-pressed={reading} onClick={() => setReading((r) => !r)}
              title={reading ? "Back to page view" : "Scroll the whole document"}>
              {reading ? "Done" : "Read"}
            </button>
          )}
        </div>
      )}
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
});

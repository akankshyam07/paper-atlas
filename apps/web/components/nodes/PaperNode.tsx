"use client";
// A paper on the board IS the document: the rendered page, readable at 100%
// zoom, not a metadata card. Books open as a two-page spread that flips.
import { memo, useCallback, useEffect, useRef, useState } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../../lib/store";
import { useBoardActions } from "../canvas/actions";
import { PdfPage } from "./PdfPage";

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
  const a = useBoardActions();
  const p = data.paper;
  const c = data.object.content as {
    pdfUrl?: string; abstract?: string; year?: number; venue?: string;
    authors?: string[]; type?: string; pageCount?: number;
    tucked?: { id: string; x: number; y: number }[];
  };
  // Most OpenAlex records have no usable OA pdf, and some "pdf" links are dead
  // or serve HTML. The abstract is a better node than a broken preview, so a
  // failed load drops the whole document UI rather than showing an error box.
  const [broken, setBroken] = useState(false);
  const onFail = useCallback(() => setBroken(true), []);
  const src = broken ? undefined : viaProxy(c.pdfUrl);
  const isBook = (c.type ?? "").includes("book");
  const [page, setPage] = useState(1);
  const [flip, setFlip] = useState<"none" | "fwd" | "back">("none");
  // Reading mode hands the document its own scrolling and text selection. Off
  // by default so the node still drags and right-clicks like a card.
  const [reading, setReading] = useState(false);
  // Page count comes from the document itself; OpenAlex does not report it.
  const [pages, setPages] = useState<number | undefined>(c.pageCount);
  const step = isBook ? 2 : 1;

  // Mount the viewer only while the node is actually on screen. A board of
  // papers otherwise starts a PDF viewer per node at once, which is what left
  // them rendering blank, and is what the PRD warns against (§21).
  const hostRef = useRef<HTMLDivElement>(null);
  const [onScreen, setOnScreen] = useState(false);
  useEffect(() => {
    const el = hostRef.current;
    if (!el) return;

    // Check position directly first. Relying on the observer's first callback
    // alone left a node that was already visible at mount showing its fallback,
    // because that callback is not guaranteed to arrive promptly inside React
    // Flow's transformed container.
    const visible = () => {
      const r = el.getBoundingClientRect();
      return r.bottom > -300 && r.top < window.innerHeight + 300;
    };
    setOnScreen(visible());

    const io = new IntersectionObserver(([e]) => setOnScreen(e.isIntersecting || visible()), {
      rootMargin: "300px",
    });
    io.observe(el);
    return () => io.disconnect();
  }, []);

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
      {/* Tucked notes ride on the paper's edge like a sticky pad — visible
          enough to remember they exist, small enough not to bury the board. */}
      {!!c.tucked?.length && (
        <button className="stickypad nodrag" onClick={() => a.tuck(id)}
          title={`${c.tucked.length} note${c.tucked.length === 1 ? "" : "s"} tucked — click to release`}>
          {c.tucked.slice(0, 3).map((t, i) => <span key={t.id} className={`pad pad-${i}`} />)}
          <span className="pad-count">{c.tucked.length}</span>
        </button>
      )}
      <div ref={hostRef} className={`sheet-stage${isBook ? " spread" : ""} flip-${flip}`}>
        {src && onScreen ? (
          isBook ? (
            <>
              <div className="leaf left"><PdfPage url={src} page={page} onPages={setPages} onFail={onFail} /></div>
              <div className="leaf right"><PdfPage url={src} page={page + 1} /></div>
            </>
          ) : (
            <div className="leaf">
              {/* Reading mode hands the whole document to the browser's viewer
                  so it scrolls; the card shows one rendered page, which is the
                  only way paging is reliable. */}
              {reading
                ? <iframe key="read" src={`${src}#toolbar=0&navpanes=0`} title={data.object.title ?? "Paper"} />
                : <PdfPage url={src} page={page} onPages={setPages} onFail={onFail} />}
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
                {isBook ? `${page}–${page + 1}` : page}{pages ? ` / ${pages}` : ""}
              </span>
              <button onClick={() => turn(1)} disabled={!!pages && page + (isBook ? 1 : 0) >= pages} aria-label="Next page">›</button>
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

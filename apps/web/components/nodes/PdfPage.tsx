"use client";
// Render PDF pages ourselves rather than embedding the browser's viewer.
//
// The embedded viewer ignored the #page fragment often enough that paging
// looked broken, and it gives no page count. Rendering to a canvas makes the
// page we ask for the page that appears, and reports how many there are.
import { useEffect, useRef, useState } from "react";

type Doc = { numPages: number; getPage: (n: number) => Promise<any> };

// One parsed document per url, shared by every node showing it: a spread would
// otherwise download and parse the same file twice.
const docs = new Map<string, Promise<Doc>>();

async function loadDoc(url: string): Promise<Doc> {
  let p = docs.get(url);
  if (!p) {
    p = (async () => {
      const pdfjs = await import("pdfjs-dist");
      // The worker is copied into public/ at the version pinned in
      // package.json. Resolving it through the bundler did not work here, and a
      // mismatched worker fails at runtime rather than at build time.
      pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";
      return await pdfjs.getDocument({ url, isEvalSupported: false }).promise;
    })();
    docs.set(url, p);
    p.catch(() => docs.delete(url)); // let a failed load be retried
  }
  return p;
}

export function PdfPage({ url, page, onPages, onFail, className }: {
  url: string;
  page: number;
  onPages?: (n: number) => void;
  onFail?: () => void;
  className?: string;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    let cancelled = false;
    let task: { cancel: () => void; promise: Promise<void> } | null = null;

    (async () => {
      try {
        const doc = await loadDoc(url);
        if (cancelled) return;
        onPages?.(doc.numPages);

        const host = hostRef.current;
        if (!host) return;
        const p = await doc.getPage(Math.min(Math.max(1, page), doc.numPages));
        if (cancelled) return;

        const width = Math.max(240, Math.round(host.getBoundingClientRect().width || 420));
        const base = p.getViewport({ scale: 1 });
        // Render at device resolution so the text is crisp, not upscaled.
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const viewport = p.getViewport({ scale: (width / base.width) * dpr });

        // Draw off-DOM, then swap the finished canvas in. pdf.js refuses a
        // second render into a canvas that is already rendering, which both a
        // double-invoked effect and a fast page turn would ask for. Swapping
        // also leaves the current page up until the next one is fully drawn, so
        // turning a page does not flash white.
        const canvas = document.createElement("canvas");
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const render = p.render({ canvasContext: ctx, viewport });
        task = render;
        await render.promise;
        if (cancelled) return;

        host.replaceChildren(canvas);
        setState("ok");
      } catch (err) {
        if (cancelled) return; // cancelling a render rejects; that is not a failure
        // Surface the reason: a silent "unavailable" hides worker and CORS
        // problems that look identical to a dead link.
        console.error("PdfPage failed", { url, page, err });
        setState("error");
        onFail?.();
      }
    })();

    return () => { cancelled = true; try { task?.cancel(); } catch { /* already done */ } };
  }, [url, page, onPages, onFail]);

  return (
    <div className={`pdfpage ${className ?? ""}`}>
      <div className="pdfpage-canvas" ref={hostRef} />
      {state === "loading" && <div className="pdfpage-state">Loading page {page}…</div>}
      {state === "error" && <div className="pdfpage-state">Preview unavailable</div>}
    </div>
  );
}

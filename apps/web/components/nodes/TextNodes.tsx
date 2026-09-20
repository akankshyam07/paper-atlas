"use client";
// Note (editable), Excerpt (quoted, keeps page + source), Thread (chat as a
// node), PDF (upload card) and Group (frame) nodes.
import { memo, useState } from "react";
import { Handle, NodeResizer, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../../lib/store";
import { useBoardActions } from "../canvas/actions";
import { QuickActions } from "./PaperNode";

const Handles = () => (
  <>
    <Handle type="target" position={Position.Left} />
    <Handle type="source" position={Position.Right} />
  </>
);

export const NoteNode = memo(function NoteNode({ id, data }: NodeProps<NodeData>) {
  const nc = data.object.content as { variant?: string; color?: string };
  const variant = nc.variant ?? "sticky";
  const color = nc.color ?? "butter";
  const a = useBoardActions();
  const text = String(data.object.content.text ?? "");
  return (
    <div className={`node note ${variant === "sticky" ? `sticky note-${color}` : ""}`}>
      <QuickActions id={id} />
      <div className="eyebrow">Note</div>
      <textarea
        className="nodrag"
        aria-label="Note text"
        defaultValue={text}
        placeholder="Write a note…"
        rows={4}
        onBlur={(e) => e.target.value !== text && a.editText(id, e.target.value)}
        style={{ width: "100%", border: 0, background: "none", resize: "vertical", marginTop: 6, fontSize: 12, lineHeight: 1.45, outline: "none" }}
      />
      <Handles />
    </div>
  );
});

export const ExcerptNode = memo(function ExcerptNode({ id, data }: NodeProps<NodeData>) {
  const a = useBoardActions();
  const page = data.object.content.pageNumber as number | undefined;
  return (
    <div className="node excerpt">
      <QuickActions id={id} />
      <div className="eyebrow">Excerpt{page ? ` · p.${page}` : ""}</div>
      <div className="node-text">“{String(data.object.content.text ?? "")}”</div>
      <Handles />
    </div>
  );
});

export const ThreadNode = memo(function ThreadNode({ id, data }: NodeProps<NodeData>) {
  const a = useBoardActions();
  const c = data.object.content as { messageCount?: number; contextCount?: number; artifactCount?: number };
  return (
    <div className="node thread">
      <QuickActions id={id} />
      <div className="eyebrow">Thread · {c.messageCount ?? 0} messages</div>
      <div className="node-title">{data.object.title}</div>
      <div className="node-sub">
        {c.contextCount ?? 0} context objects · {c.artifactCount ?? 0} artifacts
      </div>
      <Handles />
    </div>
  );
});

export const PdfNode = memo(function PdfNode({ id, data }: NodeProps<NodeData>) {
  const a = useBoardActions();
  const c = data.object.content as { filename?: string; pageCount?: number; pdfUrl?: string; abstract?: string; text?: string };
  const src = a.pdfUrl(id) ?? c.pdfUrl;
  const body = String(c.abstract ?? c.text ?? "");
  const pages = c.pageCount ?? 0;
  const [page, setPage] = useState(1);
  const go = (delta: number) => setPage((p) => Math.min(Math.max(1, p + delta), pages || Math.max(p + delta, 1)));

  return (
    <div className="node doc pdf">
      <QuickActions id={id} />
      <div className="doc-head">
        <div className="eyebrow">PDF</div>
        <div className="node-title">{data.object.title ?? c.filename}</div>
      </div>
      {src ? (
        <div className="doc-crop">
          {/* The page fragment drives the embedded viewer, so paging does not
              need the PDF to be re-fetched. */}
          <iframe key={page} src={`${src}#page=${page}&view=Fit&toolbar=0&navpanes=0`} title={data.object.title ?? "PDF"} />
        </div>
      ) : (
        <div className="doc-body">{body || "Open to read"}</div>
      )}
      {src && (
        <div className="pager" role="group" aria-label="Page navigation">
          <button onClick={() => go(-1)} disabled={page <= 1} aria-label="Previous page">‹</button>
          <span className="pager-count">{page}{pages ? ` / ${pages}` : ""}</span>
          <button onClick={() => go(1)} disabled={!!pages && page >= pages} aria-label="Next page">›</button>
        </div>
      )}
      <Handles />
    </div>
  );
});

export const GroupNode = memo(function GroupNode({ data, selected }: NodeProps<NodeData>) {
  return (
    <div className="group-node">
      <NodeResizer isVisible={selected} minWidth={200} minHeight={120} lineStyle={{ borderColor: "var(--accent)" }} />
      <div className="label eyebrow accent">{data.object.title}</div>
    </div>
  );
});

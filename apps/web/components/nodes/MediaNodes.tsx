"use client";
// Image, video, audio and generic document nodes (PRD §7). Images get view and
// zoom; the rest carry a common card with partial viewing — no editors.
import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../../lib/store";
import { QuickActions } from "./PaperNode";

type MediaContent = { url?: string; filename?: string; mime?: string; sizeBytes?: number };

function Handles() {
  return (
    <>
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </>
  );
}

const kb = (n?: number) => (!n ? "" : n > 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${Math.round(n / 1e3)} KB`);

export const ImageNode = memo(function ImageNode({ id, data }: NodeProps<NodeData>) {
  const c = data.object.content as MediaContent;
  return (
    <div className="node media">
      <QuickActions id={id} />
      {c.url
        ? <img className="media-frame" src={c.url} alt={data.object.title ?? c.filename ?? "Image"} draggable={false} />
        : <div className="media-frame empty">Image unavailable</div>}
      <div className="sheet-foot">
        <div className="sheet-title">{data.object.title ?? c.filename}</div>
        <div className="sheet-sub">Image{c.sizeBytes ? ` · ${kb(c.sizeBytes)}` : ""} · double-click to zoom</div>
      </div>
      <Handles />
    </div>
  );
});

export const VideoNode = memo(function VideoNode({ id, data }: NodeProps<NodeData>) {
  const c = data.object.content as MediaContent;
  return (
    <div className="node media">
      <QuickActions id={id} />
      {/* nodrag so scrubbing the player does not drag the node instead. */}
      {c.url
        ? <video className="media-frame nodrag" src={c.url} controls preload="metadata" />
        : <div className="media-frame empty">Video unavailable</div>}
      <div className="sheet-foot">
        <div className="sheet-title">{data.object.title ?? c.filename}</div>
        <div className="sheet-sub">Video{c.sizeBytes ? ` · ${kb(c.sizeBytes)}` : ""}</div>
      </div>
      <Handles />
    </div>
  );
});

export const AudioNode = memo(function AudioNode({ id, data }: NodeProps<NodeData>) {
  const c = data.object.content as MediaContent;
  return (
    <div className="node doc-card">
      <QuickActions id={id} />
      <div className="eyebrow">Audio</div>
      <div className="node-title">{data.object.title ?? c.filename}</div>
      {c.url && <audio className="nodrag" style={{ width: "100%", marginTop: 10 }} src={c.url} controls preload="metadata" />}
      <Handles />
    </div>
  );
});

// PRD §7: video/audio/PPT/spreadsheet/book/web share one document card.
export const DocNode = memo(function DocNode({ id, data }: NodeProps<NodeData>) {
  const c = data.object.content as MediaContent;
  const ext = (c.filename ?? "").split(".").pop()?.toUpperCase() ?? "FILE";
  return (
    <div className="node doc-card">
      <QuickActions id={id} />
      <div className="doc-icon" aria-hidden>{ext.slice(0, 4)}</div>
      <div className="node-title">{data.object.title ?? c.filename}</div>
      <div className="node-sub">{kb(c.sizeBytes)}{c.mime ? ` · ${c.mime}` : ""}</div>
      {c.url && <a className="chip click" href={c.url} target="_blank" rel="noreferrer">Open</a>}
      <Handles />
    </div>
  );
});

// Any URL as a board object: recognised providers embed their real player,
// everything else embeds directly and falls back to a link card if the site
// refuses framing (PRD §27 — no live iframe soup, one per object).
export const EmbedNode = memo(function EmbedNode({ id, data }: NodeProps<NodeData>) {
  const c = data.object.content as { url?: string; embedUrl?: string; provider?: string };
  const isVideo = c.provider === "youtube" || c.provider === "vimeo";
  return (
    <div className={`node media embed${isVideo ? " video" : ""}`}>
      <QuickActions id={id} />
      {c.embedUrl ? (
        <iframe
          className="media-frame nodrag"
          src={c.embedUrl}
          title={data.object.title ?? "Embed"}
          allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture"
          allowFullScreen
        />
      ) : (
        <div className="media-frame empty">This site cannot be embedded — open it instead.</div>
      )}
      <div className="sheet-foot">
        <div className="sheet-title">{data.object.title}</div>
        <div className="sheet-sub">
          {c.url && <a href={c.url} target="_blank" rel="noreferrer">{new URL(c.url).hostname}</a>}
        </div>
      </div>
      <Handles />
    </div>
  );
});

"use client";
// Left application rail (PRD §19, wireframe 2a): search, New canvas, recent list.
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createCanvas, listCanvases, type CanvasMeta } from "../lib/store";

export function Sidebar({ currentId, onSearch }: { currentId?: string; onSearch: () => void }) {
  const router = useRouter();
  const [recent, setRecent] = useState<CanvasMeta[]>([]);
  useEffect(() => { setRecent(listCanvases().slice(0, 12)); }, [currentId]);

  return (
    <aside className="rail">
      <div className="rail-body">
        <button className="rail-search" onClick={onSearch}>
          <span>⌕</span>Search<span className="kbd">⌘K</span>
        </button>
        <button className="rail-new" onClick={() => router.push(`/c/${createCanvas().id}`)}>+ New canvas</button>
        <div className="rail-section">RECENT</div>
        <nav className="rail-list" aria-label="Recent canvases">
          {recent.map((c) => (
            <button key={c.id} className="rail-item" aria-current={c.id === currentId ? "page" : undefined} onClick={() => router.push(`/c/${c.id}`)}>
              {c.title}
            </button>
          ))}
          {recent.length === 0 && <div className="hint" style={{ padding: "4px 9px" }}>No canvases yet</div>}
        </nav>
        <button className="rail-item" style={{ marginTop: 4 }} onClick={() => router.push("/")}>All canvases →</button>
        <div className="rail-foot">
          <div className="avatar" />
          you@lab.edu
        </div>
      </div>
    </aside>
  );
}

"use client";
// Canvas list / home (wireframe 2d): rail of views, grid of canvas cards with a
// rename/delete menu, "+ New canvas" card.
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createCanvas, deleteCanvas, listCanvases, renameCanvas, type CanvasMeta } from "../lib/store";

const VIEWS = ["All canvases", "Recent"] as const;

function ago(t: number) {
  const s = (Date.now() - t) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  if (s < 604800) return `${Math.floor(s / 86400)}d ago`;
  return `${Math.floor(s / 604800)}w ago`;
}

export function Home() {
  const router = useRouter();
  const [list, setList] = useState<CanvasMeta[] | null>(null);
  const [view, setView] = useState<(typeof VIEWS)[number]>("All canvases");
  const [menu, setMenu] = useState<string | null>(null);
  const refresh = () => setList(listCanvases());
  useEffect(() => { refresh(); }, []);
  useEffect(() => {
    // Close on an outside click only. Relying on stopPropagation alone let the
    // same click that opened the menu immediately close it again, so the menu
    // never appeared.
    const off = (e: MouseEvent) => {
      const t = e.target as HTMLElement | null;
      if (t?.closest(".card-menu") || t?.closest(".more")) return;
      setMenu(null);
    };
    document.addEventListener("click", off);
    return () => document.removeEventListener("click", off);
  }, []);

  const create = () => router.push(`/c/${createCanvas().id}`);
  const rename = (c: CanvasMeta) => {
    const t = prompt("Rename canvas", c.title);
    if (t?.trim()) { renameCanvas(c.id, t.trim()); refresh(); }
  };
  const remove = (c: CanvasMeta) => {
    if (confirm(`Delete “${c.title}”? This cannot be undone.`)) { deleteCanvas(c.id); refresh(); }
  };
  const shown = view === "Recent" ? (list ?? []).slice(0, 6) : list ?? [];

  return (
    <div className="home">
      <aside className="home-rail">
        <button className="rail-new" onClick={create}>+ New canvas</button>
        {VIEWS.map((v) => (
          <button key={v} className="rail-item" aria-current={view === v ? "page" : undefined} onClick={() => setView(v)}>{v}</button>
        ))}
      </aside>
      <main className="home-main">
        <div className="home-head">
          <h1>Your canvases</h1>
          <span className="hint">{list?.length ?? ""}</span>
          <div className="grow" />
          <span className="hint">Recent ▾</span>
        </div>
        <div className="cards">
          {shown.map((c) => (
            <div key={c.id} className="card" role="link" tabIndex={0} onClick={() => router.push(`/c/${c.id}`)} onKeyDown={(e) => e.key === "Enter" && router.push(`/c/${c.id}`)}>
              <div className="thumb" aria-hidden>
                <i style={{ left: 14, top: 14, width: 44, height: 22 }} />
                <i className="accent" style={{ left: 22, top: 44, width: 16, height: 10 }} />
                <i style={{ left: 50, top: 42, width: 28, height: 14 }} />
              </div>
              <div className="body">
                <div className="name">{c.title}</div>
                <div className="sub">{c.objectCount} object{c.objectCount === 1 ? "" : "s"} · {ago(c.updatedAt)}</div>
              </div>
              <button className="more" aria-label="Canvas menu" aria-expanded={menu === c.id} onClick={(e) => { e.stopPropagation(); setMenu(menu === c.id ? null : c.id); }}>⋯</button>
              {menu === c.id && (
                <div className="popover card-menu" style={{ position: "absolute", right: 6, top: 34, width: 150, padding: 4, zIndex: 20 }} onClick={(e) => e.stopPropagation()}>
                  <button className="menu-item" onClick={() => { setMenu(null); rename(c); }}>Rename</button>
                  <button className="menu-item danger" onClick={() => { setMenu(null); remove(c); }}>Delete</button>
                </div>
              )}
            </div>
          ))}
          <button className="card new" onClick={create}>+ New canvas</button>
        </div>
        {list && list.length === 0 && <p className="hint" style={{ marginTop: 18 }}>No canvases yet — start one and drop in a paper.</p>}
      </main>
    </div>
  );
}

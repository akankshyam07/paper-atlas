"use client";
// Interest picker (PRD §12 topic hierarchy). Tags come from OpenAlex's own
// classification rather than a hand-written list, so they match the corpus the
// recommendations are drawn from. It expands a level at a time — showing every
// tag at once would be unusable — and searching jumps straight to a topic.
import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";

export type Topic = { id: string; name: string; worksCount: number; parent?: string | null };

const KEY = "atlas.interests";

export function readInterests(): Topic[] {
  try { return JSON.parse(localStorage.getItem(KEY) ?? "[]"); } catch { return []; }
}
export function saveInterests(t: Topic[]) {
  try { localStorage.setItem(KEY, JSON.stringify(t)); } catch { /* private mode */ }
}
export function hasOnboarded() {
  try { return localStorage.getItem(KEY) !== null; } catch { return true; }
}

export function Onboarding({ onDone }: { onDone: (picked: Topic[]) => void }) {
  const [fields, setFields] = useState<Topic[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [children, setChildren] = useState<Record<string, Topic[]>>({});
  const [picked, setPicked] = useState<Topic[]>([]);
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Topic[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.topics().then((r) => setFields(r.items)).catch(() => setFields([])); }, []);

  // Search runs against topics directly, for people who know the term already.
  useEffect(() => {
    const term = q.trim();
    if (term.length < 3) { setHits([]); return; }
    let dead = false;
    const t = setTimeout(() => {
      api.topics({ q: term }).then((r) => { if (!dead) setHits(r.items); }).catch(() => {});
    }, 300);
    return () => { dead = true; clearTimeout(t); };
  }, [q]);

  const expand = useCallback(async (f: Topic) => {
    if (open === f.id) return setOpen(null);
    setOpen(f.id);
    if (children[f.id]) return;
    setBusy(true);
    try {
      const r = await api.topics({ level: "subfield", parent: f.id });
      setChildren((c) => ({ ...c, [f.id]: r.items }));
    } finally { setBusy(false); }
  }, [open, children]);

  const toggle = (t: Topic) =>
    setPicked((p) => (p.some((x) => x.id === t.id) ? p.filter((x) => x.id !== t.id) : [...p, t]));
  const isPicked = (t: Topic) => picked.some((x) => x.id === t.id);

  const finish = () => { saveInterests(picked); onDone(picked); };

  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label="Choose your interests">
      <div className="onboard" onMouseDown={(e) => e.stopPropagation()}>
        <div className="onboard-head">
          <h2>What are you interested in?</h2>
          <p>Pick a few. They shape what gets recommended.</p>
        </div>

        <input className="field onboard-search" value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Search topics — probability, CRISPR, transformers…" aria-label="Search topics" />

        <div className="onboard-body">
          {hits.length > 0 ? (
            <div className="tagwrap">
              {hits.map((t) => (
                <button key={t.id} className={`tag${isPicked(t) ? " on" : ""}`} onClick={() => toggle(t)}>
                  {t.name}{t.parent ? <span className="tag-sub">{t.parent}</span> : null}
                </button>
              ))}
            </div>
          ) : (
            fields.map((f) => (
              <div key={f.id} className="onboard-field">
                <button className={`tag lg${isPicked(f) ? " on" : ""}`} onClick={() => toggle(f)}>{f.name}</button>
                <button className="tag ghost" aria-expanded={open === f.id} onClick={() => expand(f)}>
                  {open === f.id ? "–" : "+"}
                </button>
                {open === f.id && (
                  <div className="tagwrap nested">
                    {busy && !children[f.id] && <span className="hint">Loading…</span>}
                    {(children[f.id] ?? []).map((c) => (
                      <button key={c.id} className={`tag${isPicked(c) ? " on" : ""}`} onClick={() => toggle(c)}>{c.name}</button>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="onboard-foot">
          <span className="hint">{picked.length} selected</span>
          <div className="grow" />
          <button className="btn" onClick={() => { saveInterests([]); onDone([]); }}>Skip</button>
          <button className="btn primary" disabled={picked.length === 0} onClick={finish}>Continue</button>
        </div>
      </div>
    </div>
  );
}

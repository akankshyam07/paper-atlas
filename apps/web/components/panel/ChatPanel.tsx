"use client";
// Canvas chat (PRD §17, wireframe 2i). Selected nodes are the explicit
// context; each message snapshots the context ids it was sent with. A reply
// can be saved as a note, and the whole thread can become a node.
import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../lib/store";
import { glyph } from "../search/CommandPalette";

export type ChatContext = { id: string; title: string; kind: string };

/** What the next message will be sent with. Shown wherever the user can type,
 *  because "the thing I clicked is what the AI sees" is otherwise invisible. */
export function ContextChips({ context, onFocus, onDrop, empty }: {
  context: ChatContext[];
  onFocus: (id: string) => void;
  onDrop?: (id: string) => void;
  empty?: string;
}) {
  if (context.length === 0) return empty ? <span className="ctx-empty">{empty}</span> : null;
  return (
    <>
      {context.map((c) => (
        <span key={c.id} className="ctx-chip" title={c.title}>
          <button className="ctx-go" onClick={() => onFocus(c.id)} title={`Go to “${c.title}”`}>
            <span className="glyph">{glyph(c.kind)}</span>
            <span className="ctx-t">{c.title}</span>
          </button>
          {onDrop && <button className="ctx-x" onClick={() => onDrop(c.id)} aria-label={`Remove “${c.title}” from context`}>×</button>}
        </span>
      ))}
    </>
  );
}

export function ChatPanel({ messages, context, titleOf, busy, draft, onDraft, onSend, onFocusContext, onDropContext, onSaveNote, onSaveThread, onReadAloud, onMic, recording }: {
  messages: ChatMessage[];
  context: ChatContext[];
  titleOf: (id: string) => string | undefined;
  busy: boolean;
  draft: string;
  onDraft: (v: string) => void;
  onSend: () => void;
  onFocusContext: (id: string) => void;
  onDropContext: (id: string) => void;
  onSaveNote: (m: ChatMessage) => void;
  onSaveThread: () => void;
  onReadAloud: (text: string) => void;
  onMic?: () => void;
  recording: boolean;
}) {
  const log = useRef<HTMLDivElement>(null);
  useEffect(() => { log.current?.scrollTo({ top: log.current.scrollHeight }); }, [messages.length, busy]);

  return (
    <div className="stack" style={{ height: "100%" }}>
      <div className="ctx-bar">
        <span className="ctx-label">Context</span>
        <ContextChips context={context} onFocus={onFocusContext} onDrop={onDropContext}
          empty="Select objects on the board to attach them" />
        <div className="grow" />
        <button className="btn sm" disabled={messages.length === 0} onClick={onSaveThread}>Save as node</button>
      </div>
      <div className="chat-log" ref={log}>
        {messages.length === 0 && <div className="empty">Ask about the canvas. Whatever is selected is sent as context.</div>}
        {messages.map((m) => {
          // Resolve at render time: an object deleted since the message was
          // sent should stop being named as context for it.
          const named = m.contextIds.map((id) => [id, titleOf(id)] as const).filter(([, t]) => !!t);
          return (
            <div key={m.id} className={`msg ${m.role}`}>
              {m.text}
              {named.length > 0 && (
                <div className="msg-ctx">
                  {m.role === "user" ? "asked about" : "used"}
                  {named.map(([id, t]) => (
                    <button key={id} className="ctx-ref" onClick={() => onFocusContext(id)} title={t}>{t}</button>
                  ))}
                </div>
              )}
              {m.role === "assistant" && (
                <div className="msg-actions">
                  <button className="btn primary sm" disabled={!!m.artifactId} onClick={() => onSaveNote(m)}>{m.artifactId ? "Saved" : "Save as note"}</button>
                  <button className="btn sm" onClick={() => onReadAloud(m.text)} title="Read aloud">🔊</button>
                </div>
              )}
            </div>
          );
        })}
        {busy && <div className="msg assistant"><span className="spinner" /></div>}
      </div>
      <form className="chat-reply" onSubmit={(e) => { e.preventDefault(); onSend(); }}>
        <input value={draft} onChange={(e) => onDraft(e.target.value)} placeholder="Reply…" aria-label="Reply" />
        {onMic && <button type="button" className="mic" aria-pressed={recording} onClick={onMic} title="Voice input">🎙</button>}
        <button type="submit" className="btn primary sm" disabled={!draft.trim() || busy}>Send</button>
      </form>
    </div>
  );
}

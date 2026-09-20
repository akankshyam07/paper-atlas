"use client";
// Canvas chat bar. FE builds: input + message list, uses selected nodes as context.
// Mic button = optional Deepgram voice input (SpeechProvider): record -> transcribe
// -> fill the input.
import { useState } from "react";
import { api } from "../../lib/api";

export function ChatBar() {
  const [value, setValue] = useState("");

  async function onVoice(audio: Blob) {
    // FE wires MediaRecorder to produce `audio`; then:
    setValue((await api.transcribe(audio)).text);
  }
  void onVoice; // wired when recording is added

  return (
    <div style={{ position: "absolute", bottom: 16, left: "50%", transform: "translateX(-50%)", width: 480, display: "flex", gap: 8 }}>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask about the canvas…"
        style={{ flex: 1, padding: 8, borderRadius: 8, border: "1px solid #ccc" }}
      />
      <button title="Voice (Deepgram)">🎤</button>
    </div>
  );
}

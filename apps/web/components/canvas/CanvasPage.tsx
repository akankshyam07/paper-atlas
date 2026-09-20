"use client";
import { ReactFlowProvider } from "reactflow";
import { CanvasShell } from "./CanvasShell";

export function CanvasPage({ id }: { id: string }) {
  return (
    <ReactFlowProvider>
      <CanvasShell id={id} />
    </ReactFlowProvider>
  );
}

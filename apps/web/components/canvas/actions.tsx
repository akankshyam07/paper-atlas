"use client";
// Node components can't hold callbacks in `data` (it is persisted as JSON), so
// board-level actions reach them through this context instead.
import { createContext, useContext } from "react";
import type { RecommendMode } from "@atlas/types";

export type BoardActions = {
  open: (nodeId: string) => void; // expand into the right panel
  chatAbout: (nodeId: string) => void; // start a node-scoped thread
  menu: (nodeId: string, x: number, y: number) => void; // right-click menu
  accept: (nodeId: string) => void; // suggestion ✓
  reject: (nodeId: string) => void; // suggestion ×
  more: (anchorId: string, mode: RecommendMode) => void; // "Show 3 more"
  readAloud: (text: string) => void;
  editText: (nodeId: string, text: string) => void; // inline note editing
};

const noop = () => {};
export const BoardActionsContext = createContext<BoardActions>({
  open: noop, chatAbout: noop, menu: noop, accept: noop, reject: noop, more: noop, readAloud: noop, editText: noop,
});
export const useBoardActions = () => useContext(BoardActionsContext);

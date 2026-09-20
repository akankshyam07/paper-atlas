// Deterministic placement (PRD §8): anchor is the origin, broader goes
// upstream (left), deeper goes downstream (right), lateral fans vertically,
// and nothing lands on top of an existing node.
import type { Node } from "reactflow";

export const NODE_W = 232;
export const NODE_H = 110;
const GAP = 60;

type Box = { x: number; y: number; w: number; h: number };

function size(n: Node): { w: number; h: number } {
  return { w: n.width ?? (n.style?.width as number) ?? NODE_W, h: n.height ?? (n.style?.height as number) ?? NODE_H };
}

function overlaps(a: Box, b: Box) {
  return a.x < b.x + b.w + 12 && a.x + a.w + 12 > b.x && a.y < b.y + b.h + 12 && a.y + a.h + 12 > b.y;
}

/** Slide a proposed box downward until it clears every existing node. */
export function freeSpot(box: Box, nodes: Node[]): { x: number; y: number } {
  const boxes = nodes.map((n) => ({ x: n.position.x, y: n.position.y, ...size(n) }));
  let y = box.y;
  // ponytail: linear scan, fine for the ≤100-object boards the PRD targets.
  for (let i = 0; i < 200 && boxes.some((b) => overlaps({ ...box, y }, b)); i++) y += 24;
  return { x: box.x, y };
}

/** Positions for `count` items hanging off `anchor` in a direction. */
export function fanOut(anchor: Node, count: number, dir: "left" | "right" | "down", nodes: Node[], w = NODE_W, h = NODE_H) {
  const { w: aw, h: ah } = size(anchor);
  const spread = h + 24;
  const out: { x: number; y: number }[] = [];
  const placed: Node[] = [...nodes];
  for (let i = 0; i < count; i++) {
    const offset = (i - (count - 1) / 2) * spread;
    const box =
      dir === "down"
        ? { x: anchor.position.x + (i - (count - 1) / 2) * (w + 24), y: anchor.position.y + ah + GAP, w, h }
        : { x: dir === "left" ? anchor.position.x - w - GAP : anchor.position.x + aw + GAP, y: anchor.position.y + offset, w, h };
    const p = freeSpot(box, placed);
    out.push(p);
    placed.push({ id: `tmp${i}`, position: p, data: {}, width: w, height: h });
  }
  return out;
}

/** Bounding box of a set of nodes, padded — used to size a group frame. */
export function bbox(nodes: Node[], pad = 24) {
  const xs = nodes.map((n) => n.position.x);
  const ys = nodes.map((n) => n.position.y);
  const xe = nodes.map((n) => n.position.x + size(n).w);
  const ye = nodes.map((n) => n.position.y + size(n).h);
  const x = Math.min(...xs) - pad;
  const y = Math.min(...ys) - pad - 8;
  return { x, y, w: Math.max(...xe) - x + pad, h: Math.max(...ye) - y + pad };
}

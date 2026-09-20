# Paper Atlas — YouTube Demo Script

Target length **2:45**. Voiceover is ~420 words at a normal speaking pace, so it
fits 2:30–3:00 without rushing. Screen recording is one continuous take on a
single canvas; no cuts needed except the two marked *(cut)*.

**Before recording**
- `OPENAI_API_KEY` set in `apps/api/.env`, otherwise Explain returns stub text.
- Backend on :8000, frontend on :3000, Postgres up.
- One canvas already seeded with 2–3 papers so the board is not empty on the
  second half; start the recording from the *home* screen anyway.
- Pick a topic you can narrate confidently. The script below uses
  **"sparse attention in transformers"** — swap it, but keep the same beats.
- Browser at 1440×900, zoom 100%, hide bookmarks bar.

---

## 0:00 – 0:14 — The problem

**On screen:** Home screen, then click **+ New canvas**.

> Reading into a new research area means forty browser tabs and no memory of how
> you got there. Paper Atlas makes that a canvas instead — papers, citations and
> AI notes on one board, where nothing gets lost.

## 0:14 – 0:35 — Search is real

**On screen:** Press **⌘K**, type `sparse attention transformers`, arrow down the
results, press Enter on one. The paper lands on the board; hover it so the card
shows authors, venue, citation count, open-access badge.

> Search runs against OpenAlex — two hundred and fifty million real papers. Real
> authors, real venues, real citation counts, live. Nothing here is seeded.

## 0:35 – 1:08 — Broader and Deeper *(the core idea)*

**On screen:** Right-click the paper → **Broader**. Three translucent preview
nodes fan out to the *left*. Accept one with **✓**, reject another with **×**.
Then right-click the accepted paper → **Deeper**; three more fan out to the
*right*. Let the canvas auto-fit.

> Every paper has two directions. **Broader** walks up — the surveys and
> foundational work it builds on. **Deeper** walks down — the newer, narrower
> work built on top of it. They are different pools with different scoring, not
> one "related papers" list pointed two ways.
>
> Suggestions arrive as previews. Accept it and it becomes a real node; reject it
> and it stays gone. Deeper never routes back to an ancestor, so you can walk a
> field for twenty minutes without going in circles.

## 1:08 – 1:32 — Inside a paper

**On screen:** Double-click a paper to open the viewer. Scroll the abstract;
hover a highlighted concept so the Wikipedia card pops. Click the **References**
tab, then **Cited by** — previews appear upstream and downstream.

> Open a paper and you get the real abstract, with the concepts in it linked to
> Wikipedia — so an unfamiliar term is one hover away, not another tab.
>
> References go upstream, citations go downstream, and both drop onto the same
> board as previews you accept or skip.

## 1:32 – 2:02 — AI that leaves something behind

**On screen:** Select two sentences in the abstract → **Explain**. An AI note
node appears, connected to the paper by a visible **EXPLAINS** edge. Click the
edge so the link highlights. Then open the chat bar (**✦**), ask *"what do these
three papers disagree about?"*, and drop the answer onto the canvas as a node.

> This is the part a chatbot cannot do. Ask for an explanation and you get an
> object on the board, wired back to the paper it came from. The provenance is
> the edge — you can always see which paper a claim came from.
>
> The chat sees your selection and its graph neighbours, not a blob of pasted
> text, and its answers become canvas objects too. Anything the AI wants to
> change persistently comes back as a proposal you accept or reject.

## 2:02 – 2:22 — Making it yours

**On screen (fast, no narration pauses):** marquee-select four papers → **⌘G**
group; drag the group; **Compress into stack**; draw a curved connector between
two nodes; drop a note; upload a PDF.

> Group them, stack them, connect them, annotate them, drop in your own PDFs and
> files. Undo works everywhere, and the board saves itself.

## 2:22 – 2:40 — What is under it

**On screen:** *(cut)* terminal or browser on `GET /inference/stats` showing the
savings number, then back to the canvas.

> Underneath: OpenAlex for the graph, OpenAI for the reasoning, Elastic for
> hybrid search over everything you have collected, Deepgram for voice, and Token
> Company wrapped around every model call — sixty-six percent of tokens saved on
> repeated explains, measured, not estimated.

## 2:40 – 2:50 — Close

**On screen:** Zoom out to the full canvas: papers, groups, AI notes, edges.

> Forty tabs, or this. Paper Atlas.

---

## Shot list (for the editor)

| # | Shot | Length |
|---|---|---|
| 1 | Home → new canvas | 0:14 |
| 2 | ⌘K search → paper lands | 0:21 |
| 3 | Broader → accept/reject → Deeper | 0:33 |
| 4 | Viewer: abstract, concept hover, References/Cited by | 0:24 |
| 5 | Explain → AI note + edge; chat → node | 0:30 |
| 6 | Group, stack, connector, note, upload | 0:20 |
| 7 | `/inference/stats` | 0:18 |
| 8 | Zoomed-out canvas | 0:10 |

## If you need the 60-second cut

Keep shots 1, 2, 3, 5 and 8. Broader/Deeper and the provenance edge are the two
things nobody else is showing; everything else is supporting detail.

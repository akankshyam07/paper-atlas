# Research Canvas — MVP Product Requirements Document

**Status:** Implementation-ready MVP specification  
**Primary implementation target:** Claude Code / GitHub repository  
**Product type:** AI-native visual research workspace  
**Primary corpus:** OpenAlex + user-provided documents  
**Primary reference:** WikiBoard-style visual knowledge exploration, extended with research-paper intelligence, provenance, graph-aware retrieval, and an AI canvas agent.

---

## 1. Product Summary

Research Canvas is a visual research environment for exploring a topic as a connected knowledge graph rather than as a linear list of tabs, PDFs, and chat logs.

A user works inside a **Canvas**, an infinite spatial board containing **Objects** such as research papers, excerpts, notes, Wikipedia articles, AI-generated explanations, chat threads, images, videos, and other documents. Objects can be linked with typed edges, grouped, rearranged, expanded into full viewers, and used as context for AI.

The product is centered on research papers but is deliberately modular: every meaningful piece of information can become an object, and every derived artifact should preserve where it came from.

The key product loop is:

1. Start from a question, an uploaded document, or discovery.
2. Place one or more source objects on a canvas.
3. Read, highlight, ask questions, and follow concepts/citations.
4. Expand outward with **Broader**, **Deeper**, **Supporting**, **Contradicting**, or other recommendations.
5. Accept useful suggestions into the graph and reject irrelevant ones.
6. Create notes, excerpts, AI explanations, summaries, and chat threads as linked objects.
7. Build a visible, navigable rabbit hole with provenance instead of losing research inside browser tabs or chat history.

---

## 2. Product Principles

### 2.1 Knowledge should remain spatial and inspectable
AI output must not disappear into an opaque conversation. Useful results can become first-class objects linked back to their sources.

### 2.2 Every derived object should preserve provenance
If a note, summary, excerpt, or AI artifact came from another object, the graph should show that relationship and the backend should preserve source metadata.

### 2.3 The graph should lead somewhere
Recommendations should avoid repeatedly suggesting the same semantic neighborhood. The graph should visually and semantically progress through a research rabbit hole rather than form noisy loops.

### 2.4 AI proposes; users control state
The agent may read the current canvas, reason about it, and propose mutations. Any meaningful modification to user-owned board state must be previewable and explicitly accepted, except for ephemeral UI-only operations.

### 2.5 Use existing research infrastructure before inventing new infrastructure
OpenAlex already provides works, citation links, topics, keywords, semantic search, related works, OA status, and millions of cached full-text documents. MVP should leverage these primitives rather than duplicating them.

### 2.6 Keep the MVP narrow enough to ship
The MVP must prove the central loop:
**source → explore → derive → recommend → accept → organize → continue**.

---

## 3. MVP Scope

### In scope

- User workspace and canvas list
- Create, rename, delete canvases
- Infinite/pannable/zoomable canvas
- Canvas object list / navigator
- Research paper objects
- Uploaded PDF objects
- Wikipedia article objects
- Excerpt objects
- Note objects
- AI Summary / Explanation objects
- Chat Thread objects
- Image objects
- Basic external/web objects where embeddable
- Typed edges
- Manual linking
- Grouping / frames
- Object positioning, resizing, stacking
- Full-screen or side-panel media viewers
- PDF text selection
- Highlight → excerpt
- Selected text → note
- Selected text → explain
- Selected text → ask AI
- Selected text → find related/supporting/contradicting papers
- Inline concept/Wikipedia links in parsed paper text
- OpenAlex search
- OpenAlex paper metadata
- OpenAlex citation traversal
- OpenAlex semantic search
- Broader recommendation action
- Deeper recommendation action
- Foundational paper discovery
- Recent paper discovery
- Recommendation preview nodes with accept/reject
- Canvas-level chat
- Node-scoped chat
- Thread-as-node
- Selected nodes as explicit AI context
- AI mutation proposals with approval
- Graph-aware RAG over current canvas and selected nodes
- Autosave
- Undo/redo for canvas mutations
- Basic search within a canvas

### Explicitly out of scope for MVP

- Collaborative multi-user editing
- Real-time presence
- Fine-tuning or post-training a custom foundation model
- Building a full OpenAlex mirror
- Training a custom scholarly embedding model
- Zotero/Mendeley sync
- Full citation-manager replacement
- Mobile-native apps
- iPad-native interactions
- Complex bibliography export
- Full spreadsheet editing
- Full PowerPoint editing
- Arbitrary website scraping
- Autonomous AI edits without user approval
- Long-term personalization/recommendation model trained from user behavior
- Cross-user social recommendation
- Public canvas marketplace
- Complex graph analytics / PageRank UI
- Offline mode
- OCR as a primary parsing strategy

---

## 4. Primary User Stories

### Canvas & files

1. As a user, I want to create a canvas so I have one workspace for a research rabbit hole.
2. As a user, I want to see all my canvases in a file-like navigation panel.
3. As a user, I want to rename or delete a canvas.
4. As a user, I want to pan, zoom, move, resize, group, and connect objects on a canvas.
5. As a user, I want an object navigator so I can locate items even when the board becomes large.

### Research papers

6. As a user, I want to search OpenAlex and place a paper on my canvas.
7. As a user, I want to upload a PDF and have the app identify whether it corresponds to an OpenAlex work.
8. As a user, I want to inspect a paper's authors, abstract, publication metadata, topics, citations, cited-by works, and open-access status.
9. As a user, I want to expand a paper into a readable full viewer.
10. As a user, I want citations in a paper to open candidate research-paper nodes.
11. As a user, I want to see papers that cite the current paper.
12. As a user, I want to discover broader or deeper papers from a selected paper.
13. As a user, I want to find supporting or contradicting work.

### Reading & derivation

14. As a user, I want to select text in a PDF and create an excerpt object.
15. As a user, I want to attach a note to an excerpt.
16. As a user, I want AI to explain or summarize selected text and create a linked artifact.
17. As a user, I want selected concepts to expose Wikipedia links inline.
18. As a user, I want clicking a Wikipedia concept to preview the article before adding it to the canvas.

### Chat

19. As a user, I want a canvas-level chat that can reason across the current board.
20. As a user, I want to select nodes as explicit context.
21. As a user, I want to start a thread from a node and preserve that node as initial context.
22. As a user, I want a useful chat to become its own graph node.
23. As a user, I want a thread to generate child artifacts such as notes, explanations, or paper recommendations.
24. As a user, I want separate threads to remain independent unless I explicitly invoke one from another interaction.

### AI agent

25. As a user, I want the AI to suggest organization or content changes without silently modifying my board.
26. As a user, I want to approve or reject proposed AI-created nodes, links, moves, and groups.
27. As a user, I want the AI to understand the whole canvas while prioritizing my selected nodes and current focus.

---

## 5. Core Information Model

Use a two-level model:

### 5.1 Canonical Entity
Represents an underlying source independent of a canvas.

Examples:
- OpenAlex research paper
- Wikipedia article
- Uploaded file
- External URL

A canonical entity exists once per workspace/global cache and may appear on many canvases.

### 5.2 Canvas Object
Represents one placement/instance of an entity or user-created artifact on a specific canvas.

The same paper can appear in multiple canvases with different:
- x/y position
- dimensions
- links
- groups
- notes
- local state
- collapsed/expanded state

This separation prevents duplicate scholarly metadata and keeps board state independent from source state.

---

## 6. Recommended Data Model

### users
- id UUID PK
- email
- display_name
- created_at
- updated_at

### canvases
- id UUID PK
- user_id FK
- title
- description nullable
- viewport_state JSONB
- created_at
- updated_at
- deleted_at nullable

### source_entities
- id UUID PK
- source_type enum
  - OPENALEX_WORK
  - WIKIPEDIA
  - UPLOADED_FILE
  - EXTERNAL_URL
- canonical_external_id nullable
- canonical_url nullable
- title
- metadata JSONB
- content_status enum
- created_at
- updated_at

Unique index when possible:
`(source_type, canonical_external_id)`

### openalex_works_cache
Do not duplicate all OpenAlex. Cache only works the user touches.

- source_entity_id PK/FK
- openalex_id unique
- doi nullable
- title
- abstract_text nullable
- publication_date nullable
- work_type
- language nullable
- authors JSONB
- primary_topic JSONB
- topics JSONB
- keywords JSONB
- referenced_work_ids JSONB
- cited_by_count
- related_work_ids JSONB
- open_access JSONB
- best_oa_location JSONB
- content_urls JSONB
- has_pdf
- fwci nullable
- citation_percentile JSONB nullable
- raw_payload JSONB optional
- openalex_updated_at
- cached_at

### files
- id UUID PK
- owner_user_id FK
- source_entity_id nullable
- storage_key
- filename
- mime_type
- size_bytes
- checksum_sha256
- page_count nullable
- text_extraction_status
- created_at

### canvas_objects
- id UUID PK
- canvas_id FK
- object_type enum
- source_entity_id nullable
- parent_object_id nullable
- title nullable
- content JSONB
- x float
- y float
- width float
- height float
- z_index int
- rotation float default 0
- visual_state JSONB
- created_by enum USER|AI
- created_at
- updated_at
- deleted_at nullable

### object_edges
- id UUID PK
- canvas_id FK
- source_object_id FK
- target_object_id FK
- edge_type enum
- label nullable
- direction enum DIRECTED|UNDIRECTED
- provenance enum USER|SYSTEM|AI
- confidence nullable
- metadata JSONB
- created_at

Recommended edge types:
- RELATED_TO
- CITES
- CITED_BY
- DERIVED_FROM
- EXCERPT_OF
- NOTE_ON
- EXPLAINS
- SUMMARIZES
- SUPPORTS
- CONTRADICTS
- DEFINES
- THREAD_CONTEXT
- GENERATED_FROM
- USER_LINK

The UI may render many of these using a visually simple line/arrow. Semantic type should be available in details and used by retrieval.

### groups
Implement groups as a canvas object with `object_type=GROUP`, not a separate primitive unless the canvas library strongly benefits from one.

Group content:
- name
- color/token
- description nullable
- child object IDs or use parent_object_id

### excerpts
Store excerpt-specific structured content inside canvas_objects.content:
- text
- source_object_id
- page_number
- text_start/text_end when available
- normalized_quote
- bounding_boxes[] when PDF viewer exposes coordinates
- surrounding_text optional
- created_from_selection true

### notes
- rich/plain text payload
- styling metadata
- attached source object(s) through edges

### chat_threads
- id UUID PK
- canvas_object_id unique FK
- canvas_id FK
- title
- created_at
- updated_at

### chat_messages
- id UUID PK
- thread_id FK
- role
- content
- context_snapshot JSONB
- tool_calls JSONB optional
- created_at

Important: preserve `context_snapshot` per turn. A thread may use evolving canvas context later, but historical messages should remain reproducible.

### ai_proposals
- id UUID PK
- canvas_id FK
- thread_id nullable
- proposal_type
- payload JSONB
- status PENDING|ACCEPTED|REJECTED|EXPIRED
- created_at
- resolved_at nullable

---

## 7. Object Types

### First-class MVP objects

#### Research Paper
Backed by OpenAlex when matched.

Card should show:
- title
- authors
- year
- venue/source where available
- primary topic
- cited-by count
- OA/PDF indicator

Expanded viewer:
- PDF if available
- otherwise metadata + abstract + external link
- references
- cited-by
- topics/keywords
- actions

#### PDF
User-uploaded or fetched OA PDF.

#### Excerpt
A selected passage from a source.
Always maintains source provenance.

#### Note
User-authored text with lightweight styling:
- heading
- bold
- italic
- bullets
- links

#### AI Explanation / Summary
A generated text artifact.
Must record:
- prompt/action
- source object IDs
- source excerpt IDs when applicable
- model/provider metadata
- creation timestamp

#### Chat Thread
Visual object representing a conversation.
Shows title, last message preview, linked context count.

#### Wikipedia Article
Embedded/previewable Wikipedia page.
Clicking Wikipedia hyperlinks may propose another Wikipedia node.

#### Image
Basic view and zoom.

#### Video / Audio / PPT / Spreadsheet / Book / generic web article
Represent with a common document card where practical.
For MVP, viewing support may be partial. Do not build full editors.

---

## 8. Canvas UX

Use an established graph/canvas library rather than building pan/zoom/edge behavior from scratch.

Recommended interaction model:
- infinite-feeling canvas
- wheel/pinch zoom
- click-drag pan
- draggable/resizable nodes
- selection rectangle
- multi-select
- snap guides
- edge handles
- keyboard delete
- duplicate
- undo/redo
- bring forward/send backward
- group
- collapse group
- fit selection
- fit canvas
- minimap after graph becomes non-trivial

### Layout principle
Do not auto-rearrange user-owned nodes without approval.

Recommendations may use deterministic placement:
- source node is anchor
- broader suggestions placed to one side/upstream
- deeper suggestions placed forward/downstream
- supporting/contradicting suggestions fan out laterally
- avoid placing new proposals on top of existing nodes
- use graph depth to preserve visual direction

### Suggested nodes
Suggested nodes are not persisted as accepted objects until approval.

Visual state:
- desaturated / translucent
- dotted border
- `✓` accept
- `×` reject
- hover preview
- labeled with recommendation reason

Rejected suggestions should be stored in a lightweight suppression table for that canvas/action so the same item is not immediately recommended again.

---

## 9. Object Navigator

A collapsible transparent side overlay inside a canvas.

Supports:
- all objects
- papers
- notes
- excerpts
- threads
- AI artifacts
- groups
- search
- click → focus object
- optional sort: recent / type / title

This is required because large visual boards become difficult to navigate.

---

## 10. PDF Reading and Selection

### PDF viewer
Requirements:
- page rendering
- text layer
- selectable text
- zoom
- page navigation
- search within PDF
- preserve selection location

### Selection actions
When text is selected, show a compact context menu:

**Capture**
- Highlight
- Add Note

**AI**
- Explain
- Summarize
- Ask AI

**Research**
- Related Papers
- Supporting Work
- Contradicting Work

### Highlight behavior
A persistent highlight also creates an Excerpt object in data, but it does not have to immediately appear as a large canvas card. The user can choose "Show on canvas."

### Add Note
Atomic operation:
1. Create Excerpt.
2. Create Note.
3. Link source → excerpt using EXCERPT_OF / DERIVED_FROM.
4. Link excerpt → note using NOTE_ON / DERIVED_FROM.
5. Place note near source node or in a stacked annotation presentation.

### Explain/Summarize
1. Create Excerpt if not already represented.
2. Send excerpt + local surrounding context + source metadata to LLM.
3. Create AI artifact.
4. Link artifact to excerpt with EXPLAINS or SUMMARIZES.

---

## 11. Wikipedia Concept Linking

### Goal
Make difficult or meaningful concepts inside research text explorable like Wikipedia links without turning every noun into noise.

### Extraction pipeline
Run when parsed text is first available or lazily per section/page.

1. Candidate phrase extraction
   - Prefer OpenAlex work keywords/topics where applicable.
   - Add NER/keyphrase extraction from title/abstract/full text.
   - Extract noun phrases of 1–5 words.
2. Normalize and deduplicate candidates.
3. Resolve candidates against Wikipedia search/API.
4. Keep candidates with a confident article match.
5. Rank by:
   - technical specificity
   - relevance to the source section
   - likelihood the phrase represents a learnable concept rather than ordinary language
6. Store resolved concept spans.
7. Render matched spans as blue inline links.

### Repeated concepts
Render the concept as linkable whenever it appears, but reuse one resolved concept record. Do not re-run Wikipedia resolution for each occurrence.

### Click behavior
Clicking a concept:
1. Open a lightweight article preview.
2. User can read without modifying the graph.
3. "Add to canvas" creates a Wikipedia object and `DEFINES`/`RELATED_TO` edge.

Do not automatically add Wikipedia nodes.

---

## 12. OpenAlex Integration

Use OpenAlex as the authoritative scholarly metadata/graph provider for MVP.

OpenAlex currently provides:
- 320M+ works
- authorships
- publication metadata
- abstract inverted index
- up to 3 topics per work
- work-level keywords
- topic hierarchy: domain → field → subfield → topic
- references (`referenced_works`)
- incoming citations via `cites:` queries
- `related_works`
- citation count and normalized citation metrics
- OA status
- best OA location
- downloadable PDF/TEI content for many works
- keyword search
- semantic search over title+abstract embeddings

### Do not ingest the complete OpenAlex dataset for MVP

Instead:
- query API on demand
- cache touched works
- batch-fetch referenced works when needed
- cache search/recommendation results briefly
- use background refresh only for stale objects the user opens

### Fetch strategy

#### Singleton by ID/DOI
Prefer direct work lookup. These are extremely cheap/free relative to search.

#### Search
Use OpenAlex keyword search for literal paper/title/topic lookups.

#### Semantic search
Use `search.semantic` for:
- related-paper discovery
- selected excerpts
- long descriptions
- user research intent

Do not send more than OpenAlex's useful input limit.

#### Citation traversal
Outgoing:
`referenced_works`

Incoming:
Works filtered by `cites:<work_id>`

#### Full text
Priority:
1. OpenAlex `content_urls.pdf` when available
2. `best_oa_location`
3. user upload
4. metadata-only node

Do not attempt to bypass paywalls.

### Cache TTL recommendation
- core immutable-ish metadata: 7–30 days
- citation counts: 24h–7d
- search results: 5–30 min
- fetched PDF: persistent according to allowed license/storage policy
- Wikipedia resolution: long-lived cache

---

## 13. Broader and Deeper Recommendation Semantics

This is a core product behavior and must not be implemented as two labels over the same similarity search.

### 13.1 Definitions

#### Broader
Move from the current work toward:
- more general framing
- parent research areas
- foundational or survey-level understanding
- influential work that provides prerequisite context

Examples:
- specific method → broader method family
- niche application → general domain
- new derivative technique → foundational technique
- specific empirical result → review/survey/foundational literature

#### Deeper
Move toward:
- a more specific mechanism, method, subproblem, application, or narrower research question
- high semantic similarity with increased specificity
- recent specialized developments
- a subset of the current topic

"Deeper" may include a lateral semantic move if it creates a more specialized rabbit hole, but must not merely return arbitrary related work.

### 13.2 Candidate generation

Generate candidates cheaply first, then rerank locally.

For a paper `P`:

#### Broader candidate pools
1. Papers in parent OpenAlex subfield/field with high relevance.
2. Highly cited works on P's primary topic/keywords.
3. References cited by P.
4. Surveys/reviews when type/title metadata indicates one.
5. Semantically similar works with more general topic/keyword overlap.

#### Deeper candidate pools
1. Semantic search from P's abstract or selected excerpt.
2. Works sharing P's topic plus narrower keyword overlap.
3. Recent works citing P.
4. Related works.
5. Works from sibling topics only when semantic similarity is high and the resulting concept is more specialized.

### 13.3 Feature scoring

Do not ask an LLM to discover the entire candidate set.

For each candidate calculate features such as:
- semantic relevance
- topic overlap
- keyword overlap
- hierarchy distance
- citation direction
- publication year delta
- citation influence / normalized impact
- title-type hints such as review/survey
- novelty vs existing canvas
- graph distance from existing accepted nodes
- duplicate/rejected penalty

Then rerank the top small set with an LLM only if needed to classify direction and write a one-line reason.

### 13.4 Specificity heuristic

Represent each paper as:
- primary topic
- subfield
- field
- keywords
- semantic embedding/relevance
- abstract keyphrases

Approximate broader/deeper direction using:
- hierarchy movement
- keyword specificity
- citation relationships
- generality of title/abstract
- candidate document type
- publication/citation context

LLM classifier input should contain only top candidates and compact metadata, not full papers.

Classifier output:
- BROADER
- DEEPER
- ADJACENT
- REJECT
- confidence
- short rationale

### 13.5 Avoid loops

Maintain a per-canvas recommendation frontier.

A candidate receives a strong penalty or exclusion if:
- already on canvas
- already suggested and rejected for same action
- direct ancestor of multiple recent nodes without adding new information
- semantically near-duplicate of recent accepted nodes
- causes A → B → A traversal
- points back toward the same graph depth for a "deeper" request without a meaningful specificity gain

Store `exploration_depth` and `exploration_branch_id` on accepted recommendation-derived canvas objects as UI metadata, not scholarly truth.

### 13.6 Recommendation count

Default: **3 recommendations**.

Allow "Show more" to request the next 3.

Never spray 10–20 suggestions around the board automatically.

---

## 14. Foundational and Recent Discovery

### Foundational
Use a blended score:
- semantic/topic relevance to user query
- cited_by_count
- FWCI / normalized citation percentile when available
- publication age
- reference centrality where cheaply inferable
- type/title signals for surveys, landmark methods, or seminal work

Do not equate raw citation count with foundational status.

Return 3–5 results with a short reason.

### Recent
Filter to recent publication range appropriate to field (default last 24 months, configurable).
Rank by:
- semantic/topic relevance
- normalized impact where meaningful
- citation velocity proxy (`counts_by_year`)
- recency

Do not require high absolute citation count for very new papers.

---

## 15. Retrieval / RAG Architecture

### Do not fine-tune for MVP

Fine-tuning is not needed to "teach the model what a research paper looks like." General frontier models already understand scholarly structure. The product's hard problem is access to fresh, exact, user-specific context.

MVP retrieval should combine:

1. **Explicit context**
   - selected nodes
   - active node
   - active excerpt
2. **Graph context**
   - 1-hop connected objects
   - optionally 2-hop for small graphs
   - semantically typed edges
3. **Canvas semantic context**
   - relevant chunks/objects from the current canvas
4. **External scholarly retrieval**
   - OpenAlex metadata/search/semantic search when the task requires discovery

### Chunking

For full-text PDF:
- parse page-aware text
- split primarily by document sections/headings
- fallback to ~600–1000 token chunks
- overlap ~10–15%
- store page references
- preserve paper/source ID
- preserve section title

Do not use fixed tiny chunks that destroy scholarly context.

### Embeddings

For user/canvas documents:
- use one strong general embedding model
- store in pgvector or equivalent
- embed:
  - PDF chunks
  - notes
  - excerpts
  - AI artifacts where useful
  - thread summaries, not necessarily every message

OpenAlex already handles semantic work search. Do not duplicate embeddings for all OpenAlex papers.

### Retrieval order

For a canvas AI query:
1. Active selection
2. Explicitly pinned context
3. Connected graph neighborhood
4. Semantic retrieval from canvas-local vector index
5. External OpenAlex retrieval only if user asks to discover literature or local context is insufficient

This reduces latency and prevents irrelevant global search.

### Context budget
Prefer compact object summaries and retrieved chunks. Do not serialize the entire canvas text into every prompt.

---

## 16. Canvas AI / Agent Harness

Expose canvas state to AI through a small, explicit tool surface.

Do not give the model a raw database connection.

### Read tools
- `get_canvas_summary(canvas_id)`
- `list_objects(canvas_id, filters?)`
- `get_object(object_id)`
- `get_neighbors(object_id, depth=1)`
- `get_selected_objects()`
- `search_canvas(query, filters?)`
- `get_thread(thread_id)`
- `search_openalex(query, mode, filters?)`
- `get_openalex_work(work_id)`
- `get_citations(work_id, direction)`
- `get_pdf_excerpt(object_id, location)`

### Proposal tools
These create `ai_proposals`, not direct mutations:
- `propose_create_object(...)`
- `propose_create_edge(...)`
- `propose_move_objects(...)`
- `propose_group_objects(...)`
- `propose_update_object(...)`
- `propose_delete_object(...)`

### Safe direct operations
The AI may directly perform:
- read operations
- semantic searches
- temporary previews
- recommendation generation
- draft content generation

### Approval required
User approval required for:
- persistent object creation by autonomous canvas agent
- persistent edge creation
- movement/reorganization
- grouping
- deletion
- content replacement

Exception:
If the user explicitly invokes an action whose direct outcome is obvious, e.g. "Explain selection" or "Create note," that click is itself approval to create the corresponding derived object.

### Agent response style
When suggesting graph edits, show a visual diff/proposal:
- objects to create
- edges to create
- objects to move
- groups to create
- short reason

Accept all / review individually / reject.

---

## 17. Chat Model

### Canvas chat
A persistent overlay near bottom of canvas.

Default context:
- canvas summary
- selected nodes
- current focused object
- relevant retrieved context

It does not automatically ingest all full text.

### Node-scoped chat
Starting chat from a node:
- creates a thread
- creates THREAD_CONTEXT edge from source node to thread
- source object becomes initial pinned context

### Context evolution
The thread may retrieve from current canvas state on later messages, but:
- original context links remain visible
- historical message snapshots remain immutable
- manually unlinking a graph edge does not rewrite past answers

### Thread memory
Each thread is independent.

Canvas-level chat may invoke/read a thread when the user explicitly references it or when the user selects that thread node.

No invisible memory sharing between threads.

---

## 18. Search

MVP global command/search surface should support:

### Canvas search
- title
- note/excerpt text
- paper metadata
- object type
- semantic retrieval

### OpenAlex search
- keyword search
- semantic search
- filters for year, OA, work type

Search results should be previews.
Adding a result to canvas is explicit.

---

## 19. File and Canvas Navigation

Left application sidebar:
- workspace/app logo
- New Canvas
- search canvases
- recent canvases
- canvas list
- rename/delete context menu

Inside canvas:
- floating object navigator
- canvas title
- zoom/minimap controls
- import/upload
- add object
- canvas chat bar

Autosave all board mutations.

---

## 20. API Architecture

Recommended services:

### Frontend
- React / Next.js
- TypeScript
- canvas/graph library (React Flow or equivalent)
- PDF.js for PDF rendering/text layer
- TanStack Query or equivalent for server state

### Backend
Choose one coherent backend stack. Recommended:
- Python FastAPI for AI/retrieval/document pipeline convenience
- PostgreSQL
- pgvector
- Redis optional, not required for MVP
- object storage: S3-compatible
- background jobs: lightweight queue when parsing PDFs

Alternative TypeScript backend is acceptable if team velocity is materially higher.

### Service boundaries

`CanvasService`
- CRUD canvas
- state
- object positions
- groups
- edges

`SourceService`
- canonical source entities
- deduplication

`OpenAlexService`
- API client
- caching
- search
- citations
- recommendations
- OA/fulltext

`DocumentService`
- upload
- parsing
- chunking
- PDF text coordinates

`RetrievalService`
- embeddings
- vector search
- graph-aware retrieval

`ConceptService`
- keyphrase extraction
- Wikipedia resolution
- concept span cache

`AIService`
- model gateway
- prompt construction
- tool execution
- proposal generation

`RecommendationService`
- broader/deeper/foundational/recent
- scoring
- suppression
- reranking

---

## 21. Performance Requirements

MVP target interaction budgets:

- Canvas pan/zoom/drag: 60fps on normal board sizes
- Open existing canvas shell: <1s perceived load with skeletons
- OpenAlex metadata fetch from cache: <200ms target
- uncached singleton work fetch: network-bound, optimistic UI
- canvas search: <300ms for normal workspace
- local RAG retrieval: <500ms target
- recommendation candidate generation: <1.5s target before LLM rerank
- AI response: stream immediately
- proposal rendering: incremental

### Techniques
- never send full canvas payload when a summary/selection suffices
- batch OpenAlex IDs
- use `select=` to limit fields
- cache work metadata
- debounce semantic discovery
- lazy-load PDFs
- virtualize large object lists
- do not mount full PDF/web viewers for every miniature canvas node
- use preview snapshots/cards on canvas and mount interactive viewer on focus

---

## 22. Security and Data Handling

- user uploads private by default
- signed URLs for file access
- validate MIME type and file size
- sanitize embedded HTML
- do not execute arbitrary uploaded scripts
- external webpage objects must be sandboxed
- model tools operate on scoped application APIs
- no raw DB credentials exposed to agent
- mutation tools produce proposals
- maintain audit log of AI-proposed and accepted mutations
- do not bypass publisher paywalls

---

## 23. Canonical Paper Deduplication

When a user uploads a PDF:

1. Parse DOI from metadata/text where possible.
2. Query OpenAlex by DOI.
3. Fallback fuzzy match:
   - normalized title
   - first author
   - year
4. If high-confidence match:
   - attach upload to existing canonical source entity
5. Otherwise:
   - create uploaded-file source entity
   - allow later merge

One canonical paper may have multiple source locations/files.

---

## 24. Edge UX

Semantic edges exist in data but UI must stay simple.

Default visible behavior:
- arrow/line
- optional compact label on hover
- color/style may vary by broad category, but avoid rainbow taxonomy

Suggested simplification:
- Citation
- Derivation
- Evidence
- Context
- User link

Detailed edge subtype remains available in inspector.

Users may:
- delete any edge
- change user-created semantic labels
- convert typed edge to generic user link

System-generated source facts such as OpenAlex citations should not mutate OpenAlex truth. Deleting that edge from canvas only removes the canvas representation.

---

## 25. Recommendation UI

Right-click Research Paper:

### Explore
- Broader
- Deeper
- Related papers
- Supporting work
- Contradicting work
- References
- Cited by

### AI
- Explain paper
- Summarize
- Chat about this

### Organize
- Link
- Group
- Duplicate on canvas
- Remove from canvas

Broader/Deeper action:
1. show 3 translucent suggestion nodes
2. each shows:
   - title
   - year
   - why this was suggested
   - relationship label
3. hover to inspect metadata
4. `✓` accepts node and edge
5. `×` rejects
6. `Show more` gets next batch

---

## 26. Recommendation Personalization

Not MVP.

However, capture events now so future personalization is possible:

- recommendation_shown
- recommendation_opened
- recommendation_accepted
- recommendation_rejected
- node_dwell_time bucket
- paper_opened
- action_invoked
- manual_link_created

Never let telemetry become a hidden dependency for MVP recommendation quality.

---

## 27. Wikipedia and Web Viewer Behavior

Wikipedia is a first-class supported web source.

On-canvas Wikipedia object:
- title
- lead image if available
- first paragraph/summary
- scrollable preview optional
- full viewer on expand

Do not render many live iframes simultaneously. Use cached preview representation on canvas.

For generic websites in MVP:
- URL card and safe preview
- iframe only where site policies permit
- graceful fallback to open externally

---

## 28. Undo / Version Semantics

At minimum support undo/redo for:
- create/delete object
- move/resize
- create/delete edge
- group/ungroup
- accept AI proposal

Autosave after operations.

Full historical version browsing is post-MVP.

---

## 29. Event Model

Represent canvas mutations as operations where practical:

- OBJECT_CREATED
- OBJECT_UPDATED
- OBJECT_MOVED
- OBJECT_DELETED
- EDGE_CREATED
- EDGE_DELETED
- GROUP_CREATED
- GROUP_UPDATED
- PROPOSAL_ACCEPTED
- PROPOSAL_REJECTED

This enables undo/redo, AI auditability, analytics, and future collaboration.

---

## 30. Observability

Track:
- API latency
- OpenAlex latency/errors/budget usage
- PDF parse latency/failures
- embedding latency
- AI request latency and token use
- recommendation acceptance rate
- tool failures
- proposal acceptance/rejection
- frontend render performance on large canvases

---

## 31. MVP Acceptance Criteria

### Canvas
- user can create/open/rename/delete a canvas
- pan/zoom/drag works reliably
- at least 100 lightweight objects remain usable
- edges and groups persist after refresh

### Paper
- user can search OpenAlex
- add paper to canvas
- inspect metadata
- view abstract
- inspect references
- inspect cited-by
- open OA PDF when available

### PDF
- upload PDF
- select text
- create excerpt
- add note
- explain selection
- selection provenance survives refresh

### Wikipedia
- concepts in parsed research text resolve to inline Wikipedia links
- clicking opens preview
- adding creates linked node

### Discovery
- Broader returns directionally broader candidates
- Deeper returns directionally more specific candidates
- 3 suggestions appear as proposals
- accept/reject works
- duplicates/rejected items are not immediately resurfaced

### Chat/AI
- canvas chat can use selected objects
- node-scoped thread can be created
- thread appears as node
- AI may create proposed artifacts
- mutations require approval unless triggered by an explicit direct action
- generated artifacts preserve provenance

### Retrieval
- selected nodes have highest retrieval priority
- graph neighbors are considered
- canvas semantic search works
- external OpenAlex search is only invoked when needed

---

## 32. Suggested Implementation Sequence

### Phase 0 — Repository foundation
- project structure
- database migrations
- auth shell
- context.md
- lint/typecheck/test setup
- CI

### Phase 1 — Canvas core
- canvas CRUD
- node/edge state
- object navigator
- persistence
- undo/redo
- groups

### Phase 2 — Research paper / OpenAlex
- OpenAlex client
- cache
- paper search
- paper card
- metadata viewer
- citations
- cited-by
- OA PDF loading

### Phase 3 — PDF + derived objects
- PDF.js viewer
- text selection
- excerpts
- notes
- AI explanation
- provenance

### Phase 4 — Wikipedia concepts
- candidate phrase pipeline
- Wikipedia resolver
- inline annotations
- Wikipedia node preview/add

### Phase 5 — Retrieval + chat
- document chunking
- embeddings / pgvector
- canvas retrieval
- canvas chat
- node thread
- thread node

### Phase 6 — Recommendations
- candidate generator
- broader/deeper scorer
- LLM reranker/classifier
- suggestion nodes
- accept/reject
- loop suppression

### Phase 7 — Agent mutations
- canvas tool API
- proposal system
- preview/diff
- approval

### Phase 8 — QA/polish
- performance
- edge cases
- onboarding
- keyboard shortcuts
- empty states
- accessibility
- end-to-end tests

---

## 33. Claude Code Implementation Guidance

This PRD describes product contracts and acceptance behavior. Claude Code should not treat every implementation detail as immutable if a clearly simpler or more robust implementation satisfies the same contract.

However, the following are architectural constraints:

1. Do not build a local mirror of all OpenAlex.
2. Do not fine-tune a model for MVP.
3. Preserve canonical-source vs canvas-instance separation.
4. Preserve provenance for derived artifacts.
5. Do not expose raw DB mutation access to the AI agent.
6. Persistent autonomous AI mutations require proposals/approval.
7. Selected-node context outranks whole-canvas context.
8. Broader and Deeper must use distinct directional logic.
9. Do not mount heavyweight viewers for all canvas nodes.
10. Do not automatically add recommendation or Wikipedia nodes.
11. Use tests for graph operations, provenance, retrieval ordering, and recommendation deduplication.
12. Prefer the simplest implementation that passes product acceptance tests.

When an implementation decision is not specified:
- inspect existing project conventions first
- choose a boring, well-supported library
- document material architecture decisions
- avoid speculative abstractions
- do not add features outside this MVP without a clear requirement

---

## 34. Testing Strategy

### Unit
- OpenAlex response mapping
- DOI/title dedupe
- edge semantics
- proposal validation
- graph traversal
- recommendation feature scoring
- loop suppression
- chunking
- retrieval priority
- Wikipedia candidate dedupe

### Integration
- OpenAlex client with recorded fixtures
- PDF → text → excerpt → note
- paper → citation candidate → accepted node
- AI artifact provenance
- proposal → acceptance → canvas mutation
- thread context snapshots

### E2E
Use Playwright.

Critical flows:
1. Create canvas → search paper → add.
2. Open paper → citation → add cited work.
3. Upload PDF → highlight → note.
4. Explain selection → AI artifact node.
5. Broader → accept one → reject one.
6. Deeper → ensure no duplicate/back-loop.
7. Start chat from paper → thread node.
8. Select paper + note → canvas chat references both.
9. Ask AI to organize cluster → preview → accept.
10. Refresh → state/provenance preserved.

---

## 35. Open Questions That Do Not Block MVP Coding

These can be iterated after first implementation:
- exact visual design of stacked annotations
- exact edge colors
- choice of LLM provider/model
- optional generic website embedding
- whether minimap is default-on
- exact onboarding questionnaire
- recommendation personalization
- bibliography export
- collaboration

Do not block core implementation on these.

---

## 36. Research Basis / External Dependencies

### OpenAlex
Use the official help/data/API documentation as source of truth:
- https://help.openalex.org/data/
- https://help.openalex.org/data/works/
- https://help.openalex.org/data/works/attributes/
- https://help.openalex.org/data/works/citations/
- https://help.openalex.org/data/topics/
- https://help.openalex.org/data/keywords/
- https://help.openalex.org/api/
- https://help.openalex.org/api/semantic-search/
- https://help.openalex.org/access/fulltext/

### WikiBoard references
Product inspiration only. Do not copy code or protected assets.
- https://wikiboard.org/
- Reddit product discussions supplied by the product team

Key pattern learned from WikiBoard:
- research material becomes spatial
- citations/references are navigable
- OA documents can load onto board
- concepts can open Wikipedia
- grouping/stacking/linking are essential because visual boards become messy

### Claude Code
Keep root context.md short and operational.
Use the PRD as a referenced product specification rather than stuffing all requirements into context.md.
Prefer explore → plan → implement → verify.
Use tests and browser-level validation for UI flows.

---

## 37. Sponsor Stack (HackMIT)

The product stays sponsor-agnostic at its core. Targeted sponsors are
incorporated only where they add real value, and code integrations sit **behind
modular provider interfaces** so no sponsor SDK leaks into core workflows or UI.
A sponsor SDK appears in exactly one place: its implementation under
`apps/api/providers/`. Full mapping and access info: [SPONSORS.md](./SPONSORS.md)
and [SPONSOR_CREDITS.md](./SPONSOR_CREDITS.md).

Target sponsors: OpenAI, Elastic, Dropbox, Deepgram, Token Company, Voloridge,
Long Lake, Ramp. (Not pursuing Devin.)

### Provider interfaces (code seams)
- `LLMProvider` -> **OpenAI**: agent, explain/summarize, tool calling, Broader
  vs. Deeper classification, supporting/contradicting analysis. Scoped tools, no
  direct DB access.
- `EmbeddingProvider` -> **OpenAI**: embeddings for user/canvas-local content only.
- `SearchProvider` -> **Elastic**: hybrid search over app content; canvas RAG.
  Indexes only app/user content and cached metadata; OpenAlex stays the source
  of truth and is not mirrored.
- `FileSourceProvider` -> **Dropbox**: import user research PDFs into the canvas
  through the upload/parse pipeline (UPLOADED_FILE entities). Core-fit answer to
  the Dropbox challenge.
- `SpeechProvider` -> **Deepgram** (optional): voice input to chat and read-aloud
  of AI summaries; off the core path.
- `InferenceOptimizationProvider` -> **Token Company**: caching, cheaper-model
  routing, and prompt compression around every LLM call (their LLM cost-saving
  challenge). Measuring tokens saved is the deliverable.
- `ResearchDataProvider` -> **OpenAlex** (source of truth, not a sponsor).

### Challenge alignment (no interface, product behavior)
- **Long Lake**: AI materially better than a chatbot — understands the graph,
  turns explanations into persistent objects, proposes the next direction
  visually, connects claims to papers/excerpts, reorganizes via approved actions.
- **Voloridge** ("Signal in the Noise"): the recommendation/ranking layer pulls
  high-signal papers from OpenAlex's large, noisy corpus. Optional: run heavy
  embedding/ranking on Voloridge compute. Not a data provider.
- **Ramp** ("Save Time. Save Money."): the whole product saves research time.

### Constraint (extends §33)
Do not let a sponsor SDK leak outside its provider implementation. Sponsor
services must remain replaceable after the hackathon.

"""backend-ai lane. OpenAlex API client + cache. BE #2 fills this in.

Rules (PRD §12): direct ID/DOI fetch when possible, select= to trim payload,
cache only touched works, keyword vs semantic search, never mirror all of it.
"""
# TODO(BE#2): search(query, mode), get_work(id), get_citations(id, direction).

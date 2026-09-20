"""backend-data lane. Source-entity deduplication (PRD §23). BE #1 fills this in.

On adding a paper: match by openalex_id / DOI so one canonical entity is reused
across canvases instead of duplicating scholarly metadata.
"""
# TODO(BE#1): resolve_or_create_source_entity(openalex_id | doi | title+author+year).

"""File storage. Supabase Storage for MVP (replaces the S3 line in PRD §22).

Stub: BE #1 wires the supabase-py client. Uploads are private; hand out signed
URLs on access.
"""
# TODO(BE#1): from supabase import create_client; upload(bucket, key, data) ->
# key; signed_url(key, ttl) -> url. Validate mime + size before upload.

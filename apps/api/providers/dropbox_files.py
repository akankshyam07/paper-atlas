"""Dropbox file source (Dropbox challenge). Implements FileSourceProvider.

Isolates the Dropbox SDK here so nothing else in the app imports it. A lane
builds the real OAuth + files API flow; the rest of the app calls
registry.get_file_source() and never sees Dropbox specifically.
"""
# TODO: pip install dropbox; OAuth (DROPBOX_APP_KEY/SECRET) -> list_files /
# download; feed downloaded PDFs into DocumentService upload+parse so they
# become UPLOADED_FILE source entities on the canvas (see PRD §23 dedup).

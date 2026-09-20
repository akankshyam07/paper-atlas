"""Dropbox file source (sponsor: Dropbox). Implements FileSourceProvider.

Lists and downloads the user's files so research PDFs already sitting in Dropbox
can become canvas objects through the normal upload/parse/dedup pipeline — the
Dropbox challenge in one move: fragmented files become an inspectable graph.

The SDK lives only in this file (PRD §37). Uses a long-lived access token when
one is configured, otherwise a refresh-token app credential pair.
"""
from __future__ import annotations

import os
from typing import Any

PDF_LIKE = (".pdf", ".docx", ".pptx", ".md", ".txt")


class DropboxFileSource:
    def __init__(self, token: str | None = None) -> None:
        import dropbox  # imported lazily; SDK isolated here

        token = token or os.getenv("DROPBOX_TOKEN")
        refresh = os.getenv("DROPBOX_REFRESH_TOKEN")
        app_key, app_secret = os.getenv("DROPBOX_APP_KEY"), os.getenv("DROPBOX_APP_SECRET")
        if refresh and app_key and app_secret:
            self._dbx = dropbox.Dropbox(
                oauth2_refresh_token=refresh, app_key=app_key, app_secret=app_secret
            )
        elif token:
            self._dbx = dropbox.Dropbox(token)
        else:
            raise RuntimeError("Dropbox needs DROPBOX_TOKEN or refresh-token credentials")

    def list_files(self, path: str = "") -> list[dict[str, Any]]:
        import dropbox

        res = self._dbx.files_list_folder(path or "", recursive=not path)
        entries = list(res.entries)
        while res.has_more:
            res = self._dbx.files_list_folder_continue(res.cursor)
            entries.extend(res.entries)

        out: list[dict[str, Any]] = []
        for e in entries:
            if not isinstance(e, dropbox.files.FileMetadata):
                continue
            if not e.name.lower().endswith(PDF_LIKE):
                continue
            out.append({"id": e.id, "name": e.name, "path": e.path_lower or e.path_display or ""})
        return out

    def download(self, file_id: str) -> bytes:
        # Dropbox accepts either an id:... handle or a path.
        _, res = self._dbx.files_download(file_id)
        return res.content

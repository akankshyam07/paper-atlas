"""Load apps/api/.env into the environment, once, before anything reads it.

Import this first from every entry point. Nothing here read os.environ from a
file before, so a present OPENAI_API_KEY still produced stub completions and a
present DATABASE_URL still fell through to the local docker Postgres — both
silently, because every provider is written to degrade rather than fail.

Real environment variables win: load_dotenv does not override what is already
set, so CI and deployment configuration are untouched.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def configured(name: str) -> bool:
    return bool(os.getenv(name))

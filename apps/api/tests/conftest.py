import os

# Pin the test database before main imports config, which loads .env: a
# developer's .env points at the real Supabase project, and the suite writes.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://atlas:atlas@localhost:5432/atlas")

# Run against stubs, not the sponsors' live APIs. The suite posts two bytes of
# fake audio and one-line prompts; with real credentials loaded it would bill
# the account and fail on the vendors' own validation.
# Set empty rather than deleted: config.load_dotenv would otherwise put the
# developer's real key back, since it only declines to override what is set.
for _credential in ("OPENAI_API_KEY", "DEEPGRAM_API_KEY", "ELASTIC_URL", "ELASTIC_API_KEY", "TOKEN_COMPANY_API_KEY"):
    os.environ[_credential] = ""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

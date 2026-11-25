import os

import pytest

# Tests exercise the deterministic engine; a developer's .env key must not make them call Gemini.
os.environ["OVERLORD_LIVE_LLM"] = "0"
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")


@pytest.fixture(autouse=True)
def isolated_workspace(tmp_path, monkeypatch):
    """Keep test runs out of the real compliance ledger and certificate folder."""
    import app

    monkeypatch.setattr(app, "AUDIT_RECEIPTS_PATH", str(tmp_path / "receipts" / "overlord_audit.jsonl"))
    monkeypatch.setattr(app, "CERT_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(app.gr, "Info", lambda *_a, **_kw: None)
    monkeypatch.setattr(app.gr, "Warning", lambda *_a, **_kw: None)

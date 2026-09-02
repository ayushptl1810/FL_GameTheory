import importlib
import os
import pytest


def test_dotenv_loaded_without_override(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("R2_TEST_ONLY_VAR=from_dotenv\nARCHITECT_LLM_PROVIDER=should_not_override\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ARCHITECT_LLM_PROVIDER", "already_set")
    monkeypatch.delenv("R2_TEST_ONLY_VAR", raising=False)
    import architect.llm as L
    importlib.reload(L)
    assert os.environ.get("R2_TEST_ONLY_VAR") == "from_dotenv"
    assert os.environ.get("ARCHITECT_LLM_PROVIDER") == "already_set"


def test_import_survives_missing_dotenv_and_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import architect.llm as L
    importlib.reload(L)

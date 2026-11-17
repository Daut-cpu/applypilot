import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent
TOOLS_DIR = PROJECT_DIR / "tools"

for p in [str(PROJECT_DIR), str(TOOLS_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def _fallback_config():
    """autopilot/config.json is private and gitignored: on a fresh checkout run against a
    throwaway copy of config.example.json (a copy, so a test's _cfg_write never edits the example)."""
    import shutil
    import tempfile
    import autopilot
    if autopilot.CFG.exists():
        return
    copy = Path(tempfile.mkdtemp(prefix="autopilot-test-cfg-")) / "config.json"
    shutil.copyfile(PROJECT_DIR / "autopilot" / "config.example.json", copy)
    autopilot.CFG = copy.resolve()  # read_json compares resolved paths (macOS /var -> /private/var)


_fallback_config()

import pytest


@pytest.fixture(autouse=True)
def _isolated_jobspy_cache(tmp_path, monkeypatch):
    """jobspy keeps its market cursor and caches under autopilot/cache: tests must not touch them."""
    import jobspy_fast
    monkeypatch.setattr(jobspy_fast, "CACHE_DIR", tmp_path / "jobspy-cache")


@pytest.fixture(autouse=True)
def _isolated_llm_health(tmp_path, monkeypatch):
    import autopilot
    monkeypatch.setattr(autopilot, "LLM_STATE", tmp_path / "providers.db", raising=False)
    monkeypatch.setattr(autopilot, "_LLM_BENCH", {})

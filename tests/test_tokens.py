import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from contextdiff import TokenizerUnavailableError, create_token_counter


@pytest.mark.integration
def test_real_reference_golden_counts_and_ordinary_special_text():
    # Required integration: a missing vocabulary fails this test, never skips it.
    counter = create_token_counter()
    assert counter("") == 0
    assert counter("hello") == 1
    assert counter(" world") == 1
    assert counter("hello world") == 2
    assert counter("<|endoftext|>") == 7
    assert counter("😀") == 2


def test_dependency_missing_is_recognizable(monkeypatch):
    monkeypatch.setitem(sys.modules, "tiktoken", None)
    with pytest.raises(TokenizerUnavailableError, match="Install project dependencies"):
        create_token_counter()


@pytest.mark.parametrize(
    "failure", [OSError("private path"), ValueError("private data")]
)
def test_initialization_errors_are_safe_and_recoverable(monkeypatch, failure):
    import tiktoken

    def fail(_):
        raise failure

    monkeypatch.setattr(tiktoken, "get_encoding", fail)
    with pytest.raises(TokenizerUnavailableError, match="warm-up") as error:
        create_token_counter()
    assert "private" not in str(error.value)
    assert error.value.__suppress_context__


def test_network_error_is_recognizable(monkeypatch):
    import requests
    import tiktoken

    def fail(_):
        raise requests.exceptions.ConnectionError("private network detail")

    monkeypatch.setattr(tiktoken, "get_encoding", fail)
    with pytest.raises(TokenizerUnavailableError):
        create_token_counter()


def test_unrelated_programming_errors_propagate(monkeypatch):
    import tiktoken

    def fail(_):
        raise TypeError("bug")

    monkeypatch.setattr(tiktoken, "get_encoding", fail)
    with pytest.raises(TypeError, match="bug"):
        create_token_counter()


@pytest.mark.integration
def test_fresh_process_warmed_cache_without_network():
    # Warm in the parent first; the child cannot inherit the in-memory encoding.
    create_token_counter()
    script = """
import json
import socket
from contextdiff import create_token_counter, compare_snapshots, load_json_snapshot
def deny(*args, **kwargs):
    raise AssertionError("Network attempted during warmed-cache comparison")
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny
counter = create_token_counter()
assert counter("hello world") == 2
from pathlib import Path
root = Path("tests/fixtures")
before = load_json_snapshot((root / "statuses.before.json").read_bytes())
after = load_json_snapshot((root / "statuses.after.json").read_bytes())
report = compare_snapshots(before, after, counter=counter)
assert report.tokens.status == "available"
assert report.watches[1].status == "missing_after"
print(json.dumps({"status": report.tokens.status, "watches": len(report.watches)}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"status": "available", "watches": 3}


def test_core_import_needs_neither_ui_nor_tokenizer():
    script = """
import sys
sys.modules["streamlit"] = None
sys.modules["tiktoken"] = None
from contextdiff import compare_snapshots, load_text_snapshot
before = load_text_snapshot(b"before", label="Before")
after = load_text_snapshot(b"after", label="After")
assert compare_snapshots(before, after, counter=None).tokens.status == "unavailable"
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.integration
def test_cold_cache_failure_non_token_comparison_and_warmed_recovery(tmp_path):
    create_token_counter()
    script = """
import os
import socket
from contextdiff import (
    TokenizerUnavailableError, compare_snapshots,
    create_token_counter, load_text_snapshot,
)
warmed_cache = os.environ["TIKTOKEN_CACHE_DIR"]
os.environ["TIKTOKEN_CACHE_DIR"] = os.environ["CONTEXTDIFF_COLD_TEST_CACHE"]
def deny(*args, **kwargs):
    raise OSError("Network blocked for cold-cache test")
socket.getaddrinfo = deny
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny
try:
    create_token_counter()
except TokenizerUnavailableError:
    counter = None
else:
    raise AssertionError("An empty offline cache must be unavailable")
before = load_text_snapshot(b"old", label="Before")
after = load_text_snapshot(b"new", label="After")
report = compare_snapshots(before, after, counter=counter)
assert report.tokens.status == "unavailable"
assert report.tokens.before_total is None
assert report.status_counts.modified == 1
os.environ["TIKTOKEN_CACHE_DIR"] = warmed_cache
report = compare_snapshots(before, after, counter=create_token_counter())
assert report.tokens.status == "available"
assert report.tokens.before_total == report.tokens.after_total == 1
"""
    # Record the effective default cache too, so this test works without an export.
    import tempfile

    environment = os.environ.copy()
    environment["TIKTOKEN_CACHE_DIR"] = environment.get(
        "TIKTOKEN_CACHE_DIR",
        environment.get(
            "DATA_GYM_CACHE_DIR", str(Path(tempfile.gettempdir()) / "data-gym-cache")
        ),
    )
    environment["CONTEXTDIFF_COLD_TEST_CACHE"] = str(tmp_path / "empty-cache")
    result = subprocess.run(
        [sys.executable, "-c", script],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr

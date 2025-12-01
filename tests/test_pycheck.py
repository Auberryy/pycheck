"""Tests for pycheck-tool sanity-check functionality."""
import json
import os
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch

import pycheck_tool as pycheck


def test_os_check_returns_true():
    """OS mode should return True when stdlib modules load fine."""
    result = pycheck.doSanityCheck(pycheck.OS)
    assert result is True


def test_all_check_returns_string():
    """ALL mode should return a string count of importable packages."""
    result = pycheck.doSanityCheck(pycheck.ALL)
    # result should be a non-empty string (number of packages)
    assert isinstance(result, str)
    assert int(result) > 0


def test_cli_main_runs_os_and_all(monkeypatch: MonkeyPatch):
    """CLI should return 0 when both checks pass."""
    exit_code = pycheck.main(["--os", "--all"])
    assert exit_code == 0


def test_version_exists():
    """Simple smoke test to make sure import works."""
    assert pycheck.__version__ == "0.1.1"


def test_json_flag_help(capsys: CaptureFixture[str]):
    """Check if the CLI exposes the json flag."""
    argv = ["--help"]
    with pytest.raises(SystemExit):
        pycheck.main(argv)
    captured = capsys.readouterr()
    assert "--json" in captured.out


def test_json_report_sanitizes_info(capsys: CaptureFixture[str]):
    """JSON output should not leak local paths or identifying metadata."""
    exit_code = pycheck.main(["--json"])
    assert exit_code == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    python_info = payload["python"]
    assert "executable" not in python_info
    allowed_keys = {"version", "implementation", "system", "release", "machine"}
    assert set(python_info.keys()).issubset(allowed_keys)
    username = os.environ.get("USERNAME") or os.environ.get("USER") or Path.home().name
    if username:
        assert username not in output

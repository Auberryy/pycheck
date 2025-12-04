"""Tests for pycheck-tool sanity-check functionality."""
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest import CaptureFixture, MonkeyPatch

import pycheck
from pycheck.cli import main


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
    exit_code = main(["--os", "--all"])
    assert exit_code == 0


def test_version_exists():
    """Simple smoke test to make sure import works."""
    # The package version should be the expected release version.
    assert pycheck.__version__.startswith("0.1.4")


def test_json_flag_help(capsys: CaptureFixture[str]):
    """Check if the CLI exposes the json flag."""
    argv = ["--help"]
    with pytest.raises(SystemExit):
        main(argv)
    captured = capsys.readouterr()
    assert "--json" in captured.out


def test_json_report_sanitizes_info(capsys: CaptureFixture[str]):
    """JSON output should not leak local paths or identifying metadata."""
    exit_code = main(["--json"])
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


def test_cli_debug_shows_failed_modules(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]):
    """When a module fails to import in OS mode, --debug should include failed modules in JSON output."""
    # Replace stdlib discovery to only include our mocked module
    monkeypatch.setattr("pycheck.checker._get_stdlib_modules", lambda: ["fake_broken_mod"])
    # Make the import raise ImportError for that module
    import importlib as _importlib
    orig_import = _importlib.import_module
    def fake_import(name):
        if name == "fake_broken_mod":
            raise ImportError("no such module")
        return orig_import(name)
    monkeypatch.setattr("pycheck.checker.importlib.import_module", fake_import)

    exit_code = main(["--os", "--json", "--debug"])
    assert exit_code == 1
    output = capsys.readouterr().out
    assert 'failed_imports' in output
    assert 'fake_broken_mod' in output


def test_cli_human_reads_failed_modules(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]):
    """When a module fails to import in OS mode and --debug is used, human output should list them."""
    monkeypatch.setattr("pycheck.checker._get_stdlib_modules", lambda: ["fake_broken_mod"])
    import importlib as _importlib
    orig_import = _importlib.import_module
    def fake_import(name):
        if name == "fake_broken_mod":
            raise ImportError("no such module")
        return orig_import(name)
    monkeypatch.setattr("pycheck.checker.importlib.import_module", fake_import)

    exit_code = main(["--os", "--debug"])
    assert exit_code == 1
    output = capsys.readouterr().out
    assert "Failed imports" in output
    assert "fake_broken_mod" in output


def test_ssl_failure_detection():
    """Simulate missing ssl module and ensure failure is reported."""
    with patch.dict("sys.modules", {"ssl": None}):
        result = pycheck.check_ssl_support()
    assert result["status"] == "fail"

def test_filesystem_integrity_failure():
    """Simulate a 'bit flip' where read data != written data (Should WARN)."""
    # Mock the temp directory context manager
    with patch("pycheck.checker.tempfile.TemporaryDirectory") as mock_tmp:
        mock_tmp.return_value.__enter__.return_value = "/fake/tmp"
        
        # Mock Path so we don't touch real disk
        with patch("pycheck.checker.Path") as mock_path_cls:
            mock_file = mock_path_cls.return_value.__truediv__.return_value
            
            # SCENARIO: We write correct data, but read back garbage
            mock_file.read_text.return_value = "CORRUPTED_DATA"
            
            result = pycheck.check_filesystem_access()
            
    # Verification
    assert result["status"] == "warn"
    assert "Filesystem issue" in result["detail"]
    # Ensure it caught the ValueError specifically
    assert "match" in result["detail"] or "integrity" in result["detail"]

def test_filesystem_permission_failure():
    """Simulate a permission error on the temp folder (Should FAIL)."""
    with patch("pycheck.checker.tempfile.TemporaryDirectory") as mock_tmp:
        # distinct from OSError, this should be caught as FAIL
        mock_tmp.side_effect = PermissionError("Access is denied")
        
        result = pycheck.check_filesystem_access()

    assert result["status"] == "fail"
    assert "Permission denied" in result["detail"]


def test_cli_handles_broken_package(monkeypatch: MonkeyPatch):
    """If an installed package raises an unexpected exception on import, pycheck should
    not crash - it should report a failed check and continue.
    """
    # Simulate that distributions() returns a single package 'brokenpkg'
    monkeypatch.setattr("pycheck.checker._get_all_installed_packages", lambda: ["brokenpkg"])

    # Simulate importlib.import_module raising an unexpected exception for that package
    import importlib as _importlib

    def fake_import(name):
        if name == "brokenpkg":
            raise RuntimeError("broken import during test")
        return _importlib.import_module(name)

    monkeypatch.setattr("pycheck.checker.importlib.import_module", fake_import)

    # Run the CLI (ALL mode) and ensure it does not raise - it should return exit 1 since
    # the package couldn't be imported.
    exit_code = main(["--all"])
    assert exit_code == 1


def test_corrupted_distributions_dont_crash(monkeypatch: MonkeyPatch):
    """If importlib.metadata returns corrupted distributions, pycheck should not crash."""
    class CrashingDist:
        def read_text(self, name):
            raise OSError("Disk on fire!")
        @property
        def files(self):
            raise MemoryError("Out of memory!")
        @property
        def metadata(self):
            raise SystemError("System error!")
    
    def hostile_distributions():
        yield CrashingDist()
        yield CrashingDist()
    
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata, "distributions", hostile_distributions)
    
    # This should not crash
    from pycheck.checker import _get_all_installed_packages
    result = _get_all_installed_packages()
    # Should return an empty list since all distributions are corrupted
    assert isinstance(result, list)


def test_none_module_in_sys_modules(monkeypatch: MonkeyPatch):
    """If sys.modules contains None values (which can happen), pycheck should handle it."""
    import sys
    # Temporarily add a None module
    sys.modules['_test_none_module'] = None
    try:
        # OS check should not crash
        result = pycheck.doSanityCheck(pycheck.OS)
        assert isinstance(result, bool)
    finally:
        del sys.modules['_test_none_module']
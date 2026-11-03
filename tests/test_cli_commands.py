"""CLI subprocess failures and storage lifecycle."""
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from applimiter import cli


def test_stats_closes_storage(monkeypatch, capsys):
    store = Mock()
    store.get_all_usage.return_value = []
    store.today.return_value = "2026-11-03"
    monkeypatch.setattr(cli, "load_config", lambda config: {"state_dir": "/state"})
    monkeypatch.setattr(cli, "Storage", lambda state_dir: store)

    cli.cmd_stats(SimpleNamespace(config=None, date=None))

    store.close.assert_called_once()
    assert "No usage recorded" in capsys.readouterr().out


def test_logs_propagates_failed_tail(tmp_path, monkeypatch):
    (tmp_path / "applimiter.log").write_text("log entry\n")
    monkeypatch.setattr(cli, "load_config", lambda config: {"state_dir": str(tmp_path)})

    def fail(command, **kwargs):
        assert kwargs["check"] is True
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(cli.subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        cli.cmd_logs(SimpleNamespace(config=None, follow=False, lines=10))


def test_editor_accepts_flags_and_checks_exit(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text("rules: []\n")
    monkeypatch.setenv("EDITOR", "editor --wait")
    called = []

    def run(command, **kwargs):
        called.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(cli.subprocess, "run", run)
    monkeypatch.setattr(cli, "load_config", lambda config: {"rules": []})

    cli.cmd_config_edit(SimpleNamespace(config=str(path)))

    assert called == [(["editor", "--wait", str(path)], {"check": True})]

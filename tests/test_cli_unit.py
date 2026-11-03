import argparse
import subprocess
from unittest.mock import Mock

import pytest

from applimiter import cli
from applimiter.storage import Storage


@pytest.mark.parametrize("has_usage", [False, True])
def test_stats_closes_storage(tmp_path, monkeypatch, has_usage):
    state_dir = tmp_path / "state"
    config = tmp_path / "config.yaml"
    config.write_text(f"state_dir: {state_dir}\nrules: []\n")
    if has_usage:
        seed = Storage(str(state_dir))
        seed.add_seconds("editor", "productive", 30)
        seed.close()

    instances = []

    class TrackedStorage(Storage):
        def __init__(self, path):
            super().__init__(path)
            self.closed = False
            instances.append(self)

        def close(self):
            self.closed = True
            super().close()

    monkeypatch.setattr(cli, "Storage", TrackedStorage)
    cli.cmd_stats(argparse.Namespace(config=str(config), date=None))

    assert len(instances) == 1
    assert instances[0].closed


def test_config_edit_accepts_editor_arguments(tmp_path, monkeypatch, capsys):
    config = tmp_path / "config.yaml"
    config.write_text("rules: []\n")
    monkeypatch.setenv("EDITOR", "test-editor --wait")
    runner = Mock(return_value=subprocess.CompletedProcess(["test-editor"], 0))
    monkeypatch.setattr(cli.subprocess, "run", runner)

    cli.cmd_config_edit(argparse.Namespace(config=str(config)))

    assert runner.call_args.args[0] == ["test-editor", "--wait", str(config)]
    assert "config OK" in capsys.readouterr().out


def test_config_edit_reports_nonzero_exit(tmp_path, monkeypatch, capsys):
    config = tmp_path / "config.yaml"
    config.write_text("rules: []\n")
    monkeypatch.setenv("EDITOR", "test-editor")
    runner = Mock(return_value=subprocess.CompletedProcess(["test-editor"], 2))
    monkeypatch.setattr(cli.subprocess, "run", runner)

    with pytest.raises(SystemExit) as error:
        cli.cmd_config_edit(argparse.Namespace(config=str(config)))

    assert error.value.code == 1
    assert "editor exited with status 2" in capsys.readouterr().err


def test_logs_reports_tail_exit_code(tmp_path, monkeypatch, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "applimiter.log").write_text("line\n")
    config = tmp_path / "config.yaml"
    config.write_text(f"state_dir: {state_dir}\nrules: []\n")
    runner = Mock(return_value=subprocess.CompletedProcess(["tail"], 2))
    monkeypatch.setattr(cli.subprocess, "run", runner)

    with pytest.raises(SystemExit) as error:
        cli.cmd_logs(argparse.Namespace(config=str(config), follow=False, lines=10))

    assert error.value.code == 1
    assert runner.call_args.kwargs["timeout"] == 15
    assert "tail exited with status 2" in capsys.readouterr().err


def test_logs_reports_timeout(tmp_path, monkeypatch, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "applimiter.log").write_text("line\n")
    config = tmp_path / "config.yaml"
    config.write_text(f"state_dir: {state_dir}\nrules: []\n")
    monkeypatch.setattr(
        cli.subprocess, "run",
        Mock(side_effect=subprocess.TimeoutExpired(["tail"], 15)),
    )

    with pytest.raises(SystemExit) as error:
        cli.cmd_logs(argparse.Namespace(config=str(config), follow=False, lines=10))

    assert error.value.code == 1
    assert "tail timed out" in capsys.readouterr().err

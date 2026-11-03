import subprocess
import sys
from unittest.mock import Mock

import pytest

from applimiter import service


def test_installed_user_unit_uses_active_interpreter(tmp_path, monkeypatch):
    path = tmp_path / "systemd" / "user" / "applimiter.service"
    monkeypatch.setattr(service, "UNIT_DEST", str(path))
    systemctl = Mock()
    monkeypatch.setattr(service, "_systemctl", systemctl)

    service.enable()

    unit = path.read_text()
    assert "@PYTHON_EXEC@" not in unit
    assert sys.executable in unit
    assert " -m applimiter.daemon" in unit
    assert "Restart=on-failure" in unit
    systemctl.assert_any_call("daemon-reload")
    systemctl.assert_any_call("enable", "--now", service.SERVICE_NAME)


def test_systemctl_timeout_is_reported(monkeypatch):
    runner = Mock(side_effect=subprocess.TimeoutExpired(["systemctl"], 15))
    monkeypatch.setattr(service.subprocess, "run", runner)

    with pytest.raises(service.SystemctlError, match="timed out after 15s"):
        service.start()

    assert runner.call_args.kwargs["timeout"] == 15

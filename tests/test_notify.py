import logging
import subprocess
from unittest.mock import Mock

import pytest

from applimiter import notify, policy
from applimiter.storage import Storage


@pytest.mark.parametrize("error", [
    FileNotFoundError("notify-send"),
    OSError("notification service unavailable"),
    subprocess.TimeoutExpired("notify-send", 3),
])
def test_notification_failure_does_not_skip_enforcement(tmp_path, monkeypatch, error):
    store = Storage(str(tmp_path))
    try:
        store.add_seconds("browser", "fun", 60)
        rule = {
            "name": "browser",
            "daily_limit_minutes": 1,
            "warn_at_minutes": [],
            "enforcement": "hard",
        }
        monkeypatch.setattr(notify.subprocess, "run", Mock(side_effect=error))
        blocked = Mock()
        monkeypatch.setattr(policy.actions, "block", blocked)

        policy.apply_usage_limit(rule, store)

        blocked.assert_called_once_with(rule, None)
    finally:
        store.close()


def test_nonzero_notification_exit_is_logged(monkeypatch, caplog):
    monkeypatch.setattr(
        notify.subprocess, "run",
        Mock(return_value=subprocess.CompletedProcess(["notify-send"], 2)),
    )
    with caplog.at_level(logging.WARNING, logger="applimiter"):
        notify.send("limit reached", "test")
    assert "notify-send exited with status 2" in caplog.text

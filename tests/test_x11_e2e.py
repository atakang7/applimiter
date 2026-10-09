"""Real X11/Xvfb integration: two same-name windows, only focused one may die."""
import os
import subprocess
import time

import pytest

from applimiter import actions, tracker
from applimiter.matchers import matches


def window_by_title(title):
    result = subprocess.run(
        ["xdotool", "search", "--name", "^" + title + "$"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip().splitlines()[-1] if result.returncode == 0 else None


def focus(window):
    subprocess.run(["xdotool", "windowactivate", "--sync", window], check=True, timeout=5)


@pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='requires real X11 session')
def test_real_focused_xterm_is_only_target():
    assert os.environ.get("DISPLAY"), "test needs Xvfb and a window manager"
    first = subprocess.Popen(["xterm", "-T", "APPLIMITER_FOCUSED", "-e", "sleep", "35"])
    second = subprocess.Popen(["xterm", "-T", "APPLIMITER_BACKGROUND", "-e", "sleep", "35"])
    try:
        deadline = time.monotonic() + 12
        ids = None
        while time.monotonic() < deadline:
            ids = (window_by_title("APPLIMITER_FOCUSED"),
                   window_by_title("APPLIMITER_BACKGROUND"))
            if all(ids):
                break
            time.sleep(0.2)
        assert all(ids), "two real X11 windows did not appear"

        focus(ids[0])
        sample = tracker.build_sample()
        assert sample.window_id == str(int(ids[0]))
        assert sample.active_process_name == "xterm"
        assert sample.active_pid == first.pid
        assert matches({"type": "process", "match": "xterm"}, sample)

        # Force a real focus switch between matching and enforcement.
        focus(ids[1])
        actions.block({"type": "process", "match": "xterm"}, sample)
        assert first.poll() is None
        assert second.poll() is None

        focus(ids[0])
        actions.block({"type": "process", "match": "xterm"}, sample)
        first.wait(timeout=7)
        assert second.poll() is None, "background xterm must survive hard enforcement"
    finally:
        for proc in (first, second):
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=7)

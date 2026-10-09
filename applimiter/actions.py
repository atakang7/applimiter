import logging
import os
import subprocess
from typing import Optional

import psutil

from .matchers import Sample
from .types import Rule

log = logging.getLogger("applimiter")


def _terminate_focused_process(match_name: str, sample: Sample) -> None:
    """Terminate exactly the focused, same-user process, never every match."""
    if not sample.active_pid or not sample.window_id or sample.active_process_name != match_name:
        return
    from . import tracker
    _wm_class, _title, current_pid, window_id = tracker.get_active_window()
    if current_pid != sample.active_pid or window_id != sample.window_id:
        log.info("skipping process termination: focus changed")
        return
    try:
        proc = psutil.Process(sample.active_pid)
        if (proc.pid == os.getpid() or
                proc.uids().real != os.getuid() or
                proc.name() != match_name or
                proc.create_time() != sample.active_create_time):
            log.warning("refusing to terminate process: focus or identity changed")
            return
        # Terminate rather than kill() so the application can shut down cleanly.
        proc.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        log.info("focused process already exited or not accessible")


def _close_active_chrome_tab(sample: Sample) -> None:
    if not sample.chrome_active or not sample.window_id:
        return

    # Re-sample immediately before sending keys; focus can switch between
    # the daemon's tick and enforcement, and must not close an unrelated tab.
    from . import tracker
    wm_class, title, _pid, window_id = tracker.get_active_window()
    if (window_id != sample.window_id or
            not tracker.is_chrome(wm_class) or
            (title or "").lower() != sample.title_lower):
        log.info("skipping tab close: active window changed")
        return
    try:
        # XTEST sends modifier release events; --window (XSendEvent) can leave
        # Ctrl stuck in the X server, so dispatch only to the verified focus.
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", "ctrl+w"],
            timeout=2, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        log.warning("unable to close active Chrome tab")


def block(rule: Rule, sample: Optional[Sample] = None) -> None:
    if rule["type"] not in {"process", "chrome_title"}:
        raise ValueError(f"unknown rule type: {rule['type']}")
    if sample is None:
        log.warning("refusing enforcement without a verified focused-window sample")
        return
    if rule["type"] == "process":
        _terminate_focused_process(rule["match"], sample)
    elif rule["type"] == "chrome_title":
        _close_active_chrome_tab(sample)

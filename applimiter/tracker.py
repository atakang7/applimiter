import logging
import os
import re
import subprocess
from typing import Optional, Tuple

import psutil

from .matchers import Sample

log = logging.getLogger("applimiter")
CHROME_WM_CLASSES = {"google-chrome", "chrome", "chromium", "chromium-browser"}


def get_active_window() -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str]]:
    """Return (WM_CLASS, title, owner PID, window ID), or unknown.

    X11 applications may omit _NET_WM_PID; those windows are not counted as
    native processes. We never infer a PID from another same-named process.
    """
    try:
        active = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True, text=True, timeout=2, check=False
        )
        if active.returncode != 0 or not active.stdout.strip().isdigit():
            return None, None, None, None
        window_id = active.stdout.strip()

        metadata = subprocess.run(
            ["xprop", "-id", window_id, "WM_CLASS", "_NET_WM_PID"],
            capture_output=True, text=True, timeout=2, check=False
        )
        if metadata.returncode != 0:
            return None, None, None, None

        classes = re.search(r'^WM_CLASS\(STRING\)\s*=\s*(.+)$', metadata.stdout, re.M)
        wm_class = classes.group(1).split(",")[-1].strip().strip('"').lower() if classes else None
        pid_text = re.search(r'^_NET_WM_PID\(CARDINAL\)\s*=\s*(\d+)\s*$', metadata.stdout, re.M)
        pid = int(pid_text.group(1)) if pid_text else None

        title_result = subprocess.run(
            ["xdotool", "getwindowname", window_id],
            capture_output=True, text=True, timeout=2, check=False
        )
        title = title_result.stdout.strip() if title_result.returncode == 0 else None
        return wm_class, title, pid, window_id
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None, None, None, None


def is_chrome(wm_class: Optional[str]) -> bool:
    return bool(wm_class) and wm_class in CHROME_WM_CLASSES


def build_sample() -> Sample:
    wm_class, title, pid, window_id = get_active_window()
    active_name = None
    create_time = None
    if pid is not None:
        try:
            proc = psutil.Process(pid)
            # A potentially forged X11 PID must never target another user's process.
            if proc.uids().real == os.getuid():
                active_name = proc.name()
                create_time = proc.create_time()
            else:
                pid = None
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pid = None

    return Sample(
        active_process_name=active_name,
        active_pid=pid if active_name else None,
        active_create_time=create_time,
        window_id=window_id,
        chrome_active=is_chrome(wm_class),
        title_lower=(title or "").lower(),
    )

import subprocess
from typing import Optional, Set, Tuple

import psutil

from .matchers import Sample

CHROME_WM_CLASSES = {"google-chrome", "chrome", "chromium", "chromium-browser"}


def get_running_process_names() -> Set[str]:
    names = set()

    for proc in psutil.process_iter(["name"]):
        n = proc.info.get("name")
        if n:
            names.add(n)

    return names


def get_active_window() -> Tuple[Optional[str], Optional[str]]:
    try:
        win_id = subprocess.run(
            ["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=2
        ).stdout.strip()

        if not win_id:
            return None, None

        cls = None
        xprop_out = subprocess.run(
            ["xprop", "-id", win_id, "WM_CLASS"], capture_output=True, text=True, timeout=2
        ).stdout.strip()

        # WM_CLASS(STRING) = "instance", "class" -> use the class (second value)
        if "=" in xprop_out:
            parts = [p.strip().strip('"') for p in xprop_out.split("=", 1)[1].split(",")]
            if parts:
                cls = parts[-1].lower()

        title = subprocess.run(
            ["xdotool", "getwindowname", win_id], capture_output=True, text=True, timeout=2
        ).stdout.strip()

        return cls, title
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None, None


def is_chrome(wm_class: Optional[str]) -> bool:
    return bool(wm_class) and wm_class in CHROME_WM_CLASSES


def build_sample() -> Sample:
    wm_class, title = get_active_window()

    return Sample(
        running_procs=frozenset(get_running_process_names()),
        chrome_active=is_chrome(wm_class),
        title_lower=(title or "").lower(),
    )

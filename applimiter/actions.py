import logging
import subprocess

import psutil

from .types import Rule

log = logging.getLogger("applimiter")


def _kill_process(match_name: str) -> None:
    procs = [p for p in psutil.process_iter(["name"]) if p.info.get("name") == match_name]

    for p in procs:
        try:
            p.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    _, alive = psutil.wait_procs(procs, timeout=3)

    for p in alive:
        try:
            p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def _close_active_chrome_tab() -> None:
    # `key --window <id>` sends synthetic events straight to that window via
    # XSendEvent, bypassing XTEST — the X server never sees a matching
    # modifier-release, so ctrl can appear stuck held down afterward.
    # Plain `key --clearmodifiers` goes through XTEST like a real keypress
    # (press+release for every key involved) and avoids that desync.
    try:
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+w"], timeout=2, check=False)
    except FileNotFoundError:
        log.warning("xdotool not found; cannot close tab")


_ACTIONS = {
    "process": lambda rule: _kill_process(rule["match"]),
    "chrome_title": lambda _rule: _close_active_chrome_tab(),
}


def block(rule: Rule) -> None:
    action = _ACTIONS.get(rule["type"])

    if action is None:
        raise ValueError(f"unknown rule type: {rule['type']}")

    action(rule)

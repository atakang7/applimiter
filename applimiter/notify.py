import logging
import subprocess

from .types import Rule

log = logging.getLogger("applimiter")


def send(title: str, body: str, urgency: str = "normal") -> None:
    try:
        subprocess.run(
            ["notify-send", "-u", urgency, "-a", "applimiter", title, body],
            check=False,
            timeout=3,
        )
    except FileNotFoundError:
        log.warning("notify-send not found; skipping notification: %s - %s", title, body)


def warn_threshold(rule: Rule, minutes_used: int, minutes_limit: int) -> None:
    send(f"applimiter: {rule['name']}", f"{minutes_used}m used today (limit {minutes_limit}m).")


def limit_hit(rule: Rule) -> None:
    if rule["enforcement"] == "hard":
        send(
            f"applimiter: {rule['name']} blocked",
            f"Daily limit of {rule['daily_limit_minutes']}m reached — blocked for the rest of the day.",
            urgency="critical",
        )
    else:
        send(
            f"applimiter: {rule['name']} limit reached",
            f"Daily limit of {rule['daily_limit_minutes']}m reached. (soft limit, not blocked)",
            urgency="critical",
        )


def time_locked(rule: Rule, blocked_before: str) -> None:
    send(
        f"applimiter: {rule['name']} locked",
        f"{rule['name']} is blocked until {blocked_before} today.",
        urgency="critical",
    )


def productivity_nudge(message: str, fun_minutes: int, productive_minutes: int) -> None:
    send(
        "applimiter: productivity check-in",
        message.format(fun_minutes=fun_minutes, productive_minutes=productive_minutes),
    )

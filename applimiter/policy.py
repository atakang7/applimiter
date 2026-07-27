import datetime
from typing import List, Optional

from . import actions, notify
from .storage import Storage, WarnKind
from .types import ProductivityNudge, Rule


def is_time_locked(rule: Rule, now: Optional[datetime.datetime] = None) -> bool:
    blocked_before = rule.get("blocked_before")

    if not blocked_before:
        return False

    cutoff = datetime.datetime.strptime(blocked_before, "%H:%M").time()
    now_time = (now or datetime.datetime.now()).time()

    return now_time < cutoff


def apply_time_lock(rule: Rule, store: Storage) -> bool:
    if not is_time_locked(rule):
        return False

    blocked_before = rule["blocked_before"]
    assert blocked_before is not None  # guaranteed by is_time_locked() above

    if not store.has_warned(rule["name"], WarnKind.TIME_LOCKED):
        store.mark_warned(rule["name"], WarnKind.TIME_LOCKED)
        notify.time_locked(rule, blocked_before)

    actions.block(rule)

    return True


def apply_usage_limit(rule: Rule, store: Storage) -> None:
    limit = rule.get("daily_limit_minutes")

    if limit is None:
        return

    minutes_used = store.get_seconds(rule["name"]) // 60

    for mark in rule.get("warn_at_minutes", []):
        if minutes_used >= mark and not store.has_warned(rule["name"], mark):
            store.mark_warned(rule["name"], mark)
            notify.warn_threshold(rule, minutes_used, limit)

    if minutes_used < limit:
        return

    if not store.has_warned(rule["name"], WarnKind.LIMIT_HIT):
        store.mark_warned(rule["name"], WarnKind.LIMIT_HIT)
        notify.limit_hit(rule)

    if rule["enforcement"] == "hard":
        actions.block(rule)


def apply_productivity_nudges(nudges: List[ProductivityNudge], store: Storage) -> None:
    rows = store.get_all_usage()
    fun_minutes = sum(seconds for _name, category, seconds in rows if category == "fun") // 60
    productive_minutes = sum(seconds for _name, category, seconds in rows if category == "productive") // 60

    for nudge in nudges:
        mark = nudge["minutes"]
        if fun_minutes >= mark and not store.has_nudged(mark):
            store.mark_nudged(mark)
            notify.productivity_nudge(nudge["message"], fun_minutes, productive_minutes)

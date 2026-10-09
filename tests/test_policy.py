import datetime

import pytest

from applimiter import policy
from applimiter.storage import Storage


@pytest.fixture
def store(tmp_path):
    return Storage(str(tmp_path))


@pytest.fixture
def recorder(monkeypatch):
    """Replaces actions.block and notify.send with recorders instead of hitting the OS."""
    calls = {"blocks": [], "notifications": []}
    monkeypatch.setattr(policy.actions, "block", lambda rule, sample=None: calls["blocks"].append(rule["name"]))
    monkeypatch.setattr(
        policy.notify, "send", lambda title, body, urgency="normal": calls["notifications"].append(title)
    )
    return calls


def soft_rule(**overrides):
    rule = {
        "name": "reddit",
        "type": "chrome_title",
        "match": ["reddit"],
        "category": "fun",
        "daily_limit_minutes": 20,
        "enforcement": "soft",
        "warn_at_minutes": [15],
        "blocked_before": None,
    }
    rule.update(overrides)
    return rule


def test_no_warning_below_threshold(store, recorder):
    store.add_seconds("reddit", "fun", 10 * 60)  # 10 min, warn_at 15
    policy.apply_usage_limit(soft_rule(), store)
    assert recorder["notifications"] == []
    assert recorder["blocks"] == []


def test_warns_once_when_threshold_crossed(store, recorder):
    store.add_seconds("reddit", "fun", 16 * 60)
    policy.apply_usage_limit(soft_rule(), store)
    policy.apply_usage_limit(soft_rule(), store)  # second tick, already warned
    assert recorder["notifications"].count("applimiter: reddit") == 1


def test_soft_limit_hit_notifies_but_never_blocks(store, recorder):
    store.add_seconds("reddit", "fun", 25 * 60)
    policy.apply_usage_limit(soft_rule(), store)
    assert recorder["blocks"] == []
    assert any("limit reached" in n for n in recorder["notifications"])


def test_hard_limit_hit_blocks_every_call(store, recorder):
    rule = soft_rule(name="linkedin", enforcement="hard", daily_limit_minutes=1, warn_at_minutes=[])
    store.add_seconds("linkedin", "fun", 65)  # over 1 minute
    policy.apply_usage_limit(rule, store)
    policy.apply_usage_limit(rule, store)
    policy.apply_usage_limit(rule, store)
    assert recorder["blocks"] == ["linkedin", "linkedin", "linkedin"]
    # only one "blocked" notification despite three ticks over limit
    assert recorder["notifications"].count("applimiter: linkedin blocked") == 1


def test_no_limit_configured_is_a_noop(store, recorder):
    rule = soft_rule(daily_limit_minutes=None)
    store.add_seconds("reddit", "fun", 1000)
    policy.apply_usage_limit(rule, store)
    assert recorder["blocks"] == []
    assert recorder["notifications"] == []


def test_time_lock_blocks_before_cutoff_and_warns_once(store, recorder, monkeypatch):
    rule = soft_rule(name="kick", blocked_before="17:00")
    monkeypatch.setattr(
        policy, "is_time_locked", lambda r, now=None: True
    )
    assert policy.apply_time_lock(rule, store) is True
    assert policy.apply_time_lock(rule, store) is True
    assert recorder["blocks"] == ["kick", "kick"]
    assert recorder["notifications"].count("applimiter: kick locked") == 1


def test_time_lock_inactive_after_cutoff_is_noop(store, recorder):
    rule = soft_rule(name="kick", blocked_before="00:00")  # cutoff already passed for any real time
    assert policy.apply_time_lock(rule, store) is False
    assert recorder["blocks"] == []


def test_is_time_locked_respects_cutoff():
    rule = {"blocked_before": "17:00"}
    before = datetime.datetime(2026, 1, 1, 16, 59)
    after = datetime.datetime(2026, 1, 1, 17, 0)
    assert policy.is_time_locked(rule, now=before) is True
    assert policy.is_time_locked(rule, now=after) is False


def test_is_time_locked_false_when_not_configured():
    assert policy.is_time_locked({"blocked_before": None}) is False


def test_productivity_nudge_fires_once_per_threshold(store, recorder):
    store.add_seconds("reddit", "fun", 35 * 60)
    nudges = [{"minutes": 30, "message": "{fun_minutes}m of fun"}]
    policy.apply_productivity_nudges(nudges, store)
    policy.apply_productivity_nudges(nudges, store)
    assert recorder["notifications"].count("applimiter: productivity check-in") == 1

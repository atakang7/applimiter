import pytest

from applimiter.config import ConfigError, load_config

BASE = """
rules:
  - name: steam
    type: process
    match: steam
    category: fun
    daily_limit_minutes: 60
    enforcement: hard
    warn_at_minutes: [45, 55]
"""


def write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(text)
    return str(p)


def test_valid_config_loads_and_fills_defaults(tmp_path):
    cfg = load_config(write(tmp_path, BASE))
    rule = cfg["rules"][0]
    assert rule["category"] == "fun"
    assert cfg["poll_interval"] == 5
    assert cfg["productivity_nudges"] == []


def test_chrome_title_string_match_is_normalized_to_list(tmp_path):
    text = BASE + """
  - name: youtube
    type: chrome_title
    match: youtube
    category: fun
"""
    cfg = load_config(write(tmp_path, text))
    yt = next(r for r in cfg["rules"] if r["name"] == "youtube")
    assert yt["match"] == ["youtube"]


def test_missing_rules_key_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, "poll_interval: 5\n"))


def test_unknown_rule_type_raises(tmp_path):
    text = """
rules:
  - name: bad
    type: carrier_pigeon
    match: x
"""
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, text))


def test_duplicate_rule_names_raise(tmp_path):
    text = BASE + """
  - name: steam
    type: process
    match: steam2
"""
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, text))


def test_invalid_blocked_before_format_raises(tmp_path):
    text = BASE + """
  - name: kick
    type: chrome_title
    match: kick.com
    blocked_before: "5pm"
"""
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, text))


def test_valid_blocked_before_format_accepted(tmp_path):
    text = BASE + """
  - name: kick
    type: chrome_title
    match: kick.com
    blocked_before: "17:00"
"""
    cfg = load_config(write(tmp_path, text))
    kick = next(r for r in cfg["rules"] if r["name"] == "kick")
    assert kick["blocked_before"] == "17:00"


def test_unknown_enforcement_raises(tmp_path):
    text = BASE + """
  - name: bad
    type: process
    match: x
    enforcement: destroy
"""
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, text))


def test_negative_daily_limit_raises(tmp_path):
    text = BASE + """
  - name: bad
    type: process
    match: x
    daily_limit_minutes: -5
"""
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, text))

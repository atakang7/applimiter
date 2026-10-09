import os
import re
from typing import Optional

import yaml

from .types import Config, Rule

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/applimiter/config.yaml")
KNOWN_RULE_TYPES = {"process", "chrome_title"}
KNOWN_ENFORCEMENTS = {"soft", "hard"}
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class ConfigError(ValueError):
    pass


def _find_config_path(explicit: Optional[str] = None) -> str:
    if explicit:
        return os.path.expanduser(explicit)

    if os.path.exists(DEFAULT_CONFIG_PATH):
        return DEFAULT_CONFIG_PATH

    local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    if os.path.exists(local):
        return local

    raise FileNotFoundError(
        f"No config found at {DEFAULT_CONFIG_PATH} or {local}. Create one (see config.yaml example)."
    )


def _validate_rule(rule: Rule, index: int) -> None:
    where = f"rules[{index}]" + (f" ({rule['name']})" if "name" in rule else "")

    if "name" not in rule:
        raise ConfigError(f"{where}: missing required field 'name'")
    if not isinstance(rule["name"], str) or not rule["name"].strip():
        raise ConfigError(f"{where}: name must be a non-empty string")
    if "type" not in rule:
        raise ConfigError(f"{where}: missing required field 'type'")
    if rule["type"] not in KNOWN_RULE_TYPES:
        raise ConfigError(f"{where}: unknown type '{rule['type']}', expected one of {sorted(KNOWN_RULE_TYPES)}")
    if "match" not in rule:
        raise ConfigError(f"{where}: missing required field 'match'")
    if rule["type"] == "process":
        if not isinstance(rule["match"], str) or not rule["match"].strip():
            raise ConfigError(f"{where}: 'match' for type 'process' must be a non-empty string")
    else:
        if (not isinstance(rule["match"], list) or not rule["match"]
                or any(not isinstance(value, str) or not value.strip() for value in rule["match"])):
            raise ConfigError(f"{where}: 'match' for type 'chrome_title' must be a non-empty list of strings")

    if rule["enforcement"] not in KNOWN_ENFORCEMENTS:
        raise ConfigError(f"{where}: unknown enforcement '{rule['enforcement']}', expected one of {sorted(KNOWN_ENFORCEMENTS)}")

    limit = rule["daily_limit_minutes"]
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ConfigError(f"{where}: daily_limit_minutes must be a positive integer")

    warnings = rule["warn_at_minutes"]
    if (not isinstance(warnings, list) or
            any(type(value) is not int or value < 0 for value in warnings)):
        raise ConfigError(f"{where}: warn_at_minutes must be a list of non-negative integers")

    if rule["blocked_before"] is not None and not TIME_RE.match(str(rule["blocked_before"])):
        raise ConfigError(f"{where}: blocked_before must be 'HH:MM' 24h format, got {rule['blocked_before']!r}")


def load_config(path: Optional[str] = None) -> Config:
    config_path = _find_config_path(path)

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict) or not isinstance(raw.get("rules"), list):
        raise ConfigError(f"{config_path}: config must define a top-level 'rules' list")

    state_dir = raw.get("state_dir", "~/.local/share/applimiter")
    if not isinstance(state_dir, str) or not state_dir.strip():
        raise ConfigError(f"{config_path}: state_dir must be a non-empty path")
    raw["state_dir"] = os.path.expanduser(state_dir)

    interval = raw.get("poll_interval", 5)
    if type(interval) is not int or interval <= 0:
        raise ConfigError(f"{config_path}: poll_interval must be a positive integer")
    raw["poll_interval"] = interval

    names_seen = set()
    for i, rule in enumerate(raw["rules"]):
        if not isinstance(rule, dict):
            raise ConfigError(f"rules[{i}]: expected a mapping")
        rule.setdefault("category", "uncategorized")
        rule.setdefault("daily_limit_minutes", None)
        rule.setdefault("enforcement", "soft")
        rule.setdefault("warn_at_minutes", [])
        rule.setdefault("blocked_before", None)
        if rule.get("type") == "chrome_title" and isinstance(rule.get("match"), str):
            rule["match"] = [rule["match"]]

        _validate_rule(rule, i)

        if rule["name"] in names_seen:
            raise ConfigError(f"rules[{i}]: duplicate rule name '{rule['name']}'")
        names_seen.add(rule["name"])

    raw.setdefault("productivity_nudges", [])

    return raw

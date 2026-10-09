from dataclasses import dataclass
from typing import Optional

from .types import Rule


@dataclass(frozen=True)
class Sample:
    # Only the focused window counts as screen time. Process existence is
    # insufficient: a background editor must not accrue hours or be killed.
    active_process_name: Optional[str] = None
    active_pid: Optional[int] = None
    active_create_time: Optional[float] = None
    window_id: Optional[str] = None
    chrome_active: bool = False
    title_lower: str = ""


def _match_process(rule: Rule, sample: Sample) -> bool:
    return rule["match"] == sample.active_process_name and sample.active_pid is not None


def _match_chrome_title(rule: Rule, sample: Sample) -> bool:
    return sample.chrome_active and bool(sample.window_id) and any(
        kw.lower() in sample.title_lower for kw in rule["match"]
    )


_MATCHERS = {
    "process": _match_process,
    "chrome_title": _match_chrome_title,
}


def matches(rule: Rule, sample: Sample) -> bool:
    matcher = _MATCHERS.get(rule["type"])
    if matcher is None:
        raise ValueError(f"unknown rule type: {rule['type']}")
    return matcher(rule, sample)

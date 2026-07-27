from dataclasses import dataclass

from .types import Rule


@dataclass(frozen=True)
class Sample:
    running_procs: frozenset[str]
    chrome_active: bool
    title_lower: str


def _match_process(rule: Rule, sample: Sample) -> bool:
    return rule["match"] in sample.running_procs


def _match_chrome_title(rule: Rule, sample: Sample) -> bool:
    return sample.chrome_active and any(kw.lower() in sample.title_lower for kw in rule["match"])


_MATCHERS = {
    "process": _match_process,
    "chrome_title": _match_chrome_title,
}


def matches(rule: Rule, sample: Sample) -> bool:
    matcher = _MATCHERS.get(rule["type"])

    if matcher is None:
        raise ValueError(f"unknown rule type: {rule['type']}")

    return matcher(rule, sample)

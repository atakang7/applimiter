from typing import List, Optional, TypedDict, Union


class Rule(TypedDict):
    name: str
    type: str
    match: Union[str, List[str]]
    category: str
    daily_limit_minutes: Optional[int]
    enforcement: str
    warn_at_minutes: List[int]
    blocked_before: Optional[str]


class ProductivityNudge(TypedDict):
    minutes: int
    message: str


class Config(TypedDict):
    state_dir: str
    poll_interval: int
    rules: List[Rule]
    productivity_nudges: List[ProductivityNudge]

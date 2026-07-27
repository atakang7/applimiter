import pytest

from applimiter.matchers import Sample, matches


def make_sample(procs=(), chrome_active=False, title=""):
    return Sample(running_procs=frozenset(procs), chrome_active=chrome_active, title_lower=title.lower())


def test_process_rule_matches_running_process():
    rule = {"type": "process", "match": "steam"}
    assert matches(rule, make_sample(procs={"steam", "bash"}))


def test_process_rule_does_not_match_absent_process():
    rule = {"type": "process", "match": "steam"}
    assert not matches(rule, make_sample(procs={"bash"}))


def test_chrome_title_rule_requires_chrome_focused():
    rule = {"type": "chrome_title", "match": ["youtube"]}
    sample = make_sample(chrome_active=False, title="YouTube - Google Chrome")
    assert not matches(rule, sample)


def test_chrome_title_rule_matches_keyword_case_insensitively():
    rule = {"type": "chrome_title", "match": ["youtube"]}
    sample = make_sample(chrome_active=True, title="Some Video - YouTube - Google Chrome")
    assert matches(rule, sample)


def test_chrome_title_rule_matches_any_of_multiple_keywords():
    rule = {"type": "chrome_title", "match": ["twitter", "x.com", " / x"]}
    sample = make_sample(chrome_active=True, title="Home / X")
    assert matches(rule, sample)


def test_chrome_title_rule_no_match_when_keyword_absent():
    rule = {"type": "chrome_title", "match": ["reddit"]}
    sample = make_sample(chrome_active=True, title="Inbox - Gmail")
    assert not matches(rule, sample)


def test_unknown_rule_type_raises():
    rule = {"type": "carrier_pigeon", "match": "x"}
    with pytest.raises(ValueError):
        matches(rule, make_sample())

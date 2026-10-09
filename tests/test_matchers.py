import pytest

from applimiter.matchers import Sample, matches


def make_sample(process=None, pid=None, chrome_active=False, title="", window_id="100"):
    return Sample(
        active_process_name=process,
        active_pid=pid,
        chrome_active=chrome_active,
        title_lower=title.lower(),
        window_id=window_id,
    )


def test_process_rule_requires_foreground_process_and_pid():
    rule = {"type": "process", "match": "steam"}
    assert matches(rule, make_sample(process="steam", pid=111))
    assert not matches(rule, make_sample(process="steam", pid=None))
    assert not matches(rule, make_sample(process="bash", pid=222))
    assert not matches(rule, make_sample())


def test_chrome_title_rule_requires_chrome_focused():
    rule = {"type": "chrome_title", "match": ["youtube"]}
    assert not matches(rule, make_sample(title="YouTube - Chrome"))
    assert matches(rule, make_sample(chrome_active=True, title="YouTube - Chrome"))
    assert not matches(rule, make_sample(chrome_active=True, title="YouTube - Chrome", window_id=None))


def test_chrome_title_rule_matches_keyword_case_insensitively():
    rule = {"type": "chrome_title", "match": ["youtube"]}
    assert matches(rule, make_sample(chrome_active=True, title="Some Video - YouTube - Chrome"))


def test_chrome_title_rule_matches_any_keyword():
    rule = {"type": "chrome_title", "match": ["twitter", "x.com", " / x"]}
    assert matches(rule, make_sample(chrome_active=True, title="Home / X"))


def test_chrome_title_rule_no_match_when_keyword_absent():
    rule = {"type": "chrome_title", "match": ["reddit"]}
    assert not matches(rule, make_sample(chrome_active=True, title="Inbox - Gmail"))


def test_unknown_rule_type_raises():
    with pytest.raises(ValueError):
        matches({"type": "carrier_pigeon", "match": "x"}, make_sample())

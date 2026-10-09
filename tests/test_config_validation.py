import pytest

from applimiter.config import ConfigError, load_config


BASE = """
rules:
  - name: chrome
    type: chrome_title
    match: ["youtube"]
"""


@pytest.mark.parametrize(
    "document",
    [
        "[]",
        "null",
        "rules: null",
        "rules: {}",
        "rules:\n  - not-a-mapping",
        "poll_interval: 0\n" + BASE,
        "poll_interval: -1\n" + BASE,
        "poll_interval: abc\n" + BASE,
        "state_dir: []\n" + BASE,
        BASE.replace('["youtube"]', "[]"),
        BASE.replace('["youtube"]', '[42]'),
        BASE.replace("name: chrome", "name: ''"),
        BASE + "  - name: bad\n    type: process\n    match: ''\n",
        BASE + "  - name: bad\n    type: process\n    match: code\n    daily_limit_minutes: 'five'\n",
        BASE + "  - name: bad\n    type: process\n    match: code\n    warn_at_minutes: [a]\n",
    ],
)
def test_invalid_config_is_reported_as_config_error(tmp_path, document):
    path = tmp_path / "config.yaml"
    path.write_text(document)
    with pytest.raises(ConfigError):
        load_config(str(path))


def test_valid_minimal_configuration(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(BASE)
    cfg = load_config(str(path))
    assert cfg["poll_interval"] == 5
    assert cfg["rules"][0]["match"] == ["youtube"]


@pytest.mark.parametrize("document", [
    "rules: []\nproductivity_nudges: nope\n",
    "rules: []\nproductivity_nudges:\n  - minutes: 0\n    message: Hello\n",
    "rules: []\nproductivity_nudges:\n  - minutes: 3\n    message: '{unknown}'\n",
    "rules: []\nproductivity_nudges:\n  - minutes: 3\n    message: '{fun_minutes.__class__}'\n",
    "rules: []\nproductivity_nudges:\n  - minutes: 3\n    message: valid\n  - minutes: 3\n    message: duplicate\n",
    "rules:\n  - name: test\n    type: [process]\n    match: x\n",
    "rules:\n  - name: test\n    type: process\n    match: x\n    category: []\n",
    "rules: [\n",
])
def test_invalid_or_dangerous_configs_fail_gracefully(tmp_path, document):
    path = tmp_path / "config.yaml"
    path.write_text(document)
    with pytest.raises(ConfigError):
        load_config(str(path))


def test_nudge_formatting_accepted(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "rules: []\nproductivity_nudges:\n  - minutes: 10\n"
        "    message: '{fun_minutes}m fun, {productive_minutes}m work'\n"
    )
    assert load_config(str(path))["productivity_nudges"][0]["minutes"] == 10

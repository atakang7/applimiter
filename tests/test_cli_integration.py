"""Exercise the installed CLI against an isolated SQLite usage store."""

import subprocess
import sys

from applimiter.storage import Storage


def run_cli(config, *args):
    return subprocess.run(
        [sys.executable, "-m", "applimiter", "--config", str(config), *args],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_config_validate_and_stats_end_to_end(tmp_path):
    state_dir = tmp_path / "state"
    config = tmp_path / "config.yaml"
    config.write_text(
        f"state_dir: {state_dir}\n"
        "rules:\n"
        "  - name: youtube\n"
        "    type: chrome_title\n"
        "    match: [youtube]\n"
        "    category: fun\n"
        "    daily_limit_minutes: 10\n"
    )

    validated = run_cli(config, "config", "validate")
    assert validated.returncode == 0, validated.stderr
    assert "config OK" in validated.stdout

    store = Storage(str(state_dir))
    store.add_seconds("youtube", "fun", 125)
    store.conn.close()

    reported = run_cli(config, "stats")
    assert reported.returncode == 0, reported.stderr
    assert "youtube" in reported.stdout
    assert "2m05s" in reported.stdout
    assert "Fun time:" in reported.stdout


def test_invalid_config_exits_nonzero(tmp_path):
    config = tmp_path / "bad.yaml"
    config.write_text("poll_interval: 0\nrules: []\n")
    result = run_cli(config, "config", "validate")
    assert result.returncode == 1
    assert "poll_interval must be a positive integer" in result.stderr

"""Safety and integration tests. They never kill unrelated user processes."""
import os
import subprocess
import sys
from unittest.mock import Mock

import psutil
import pytest

from applimiter import actions, tracker
from applimiter.daemon import Daemon
from applimiter.matchers import Sample
from applimiter.storage import Storage


def test_foreground_process_identity_and_same_user_enforced(monkeypatch):
    first = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(25)"])
    second = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(25)"])
    try:
        first_proc = psutil.Process(first.pid)
        monkeypatch.setattr(tracker, 'get_active_window', lambda: ('xterm', 'Test', first.pid, '321'))
        sample = Sample(
            active_process_name=first_proc.name(),
            active_pid=first.pid,
            active_create_time=first_proc.create_time(),
            window_id='321',
        )
        rule = {"type": "process", "match": first_proc.name()}
        # A reused PID or a mismatched title MUST NOT be terminated.
        actions.block(rule, Sample(
            active_process_name=first_proc.name(), active_pid=first.pid,
            active_create_time=first_proc.create_time() - 100,
            window_id='321',
        ))
        assert first.poll() is None
        actions.block(rule, sample)
        first.wait(timeout=7)
        assert first.returncode is not None
        assert second.poll() is None, "enforcement must not kill another same-name process"
    finally:
        for child in (first, second):
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=7)


def test_changed_chrome_focus_is_never_closed(monkeypatch):
    sample = Sample(chrome_active=True, window_id="123", title_lower="youtube")
    monkeypatch.setattr(tracker, "get_active_window", lambda: ("google-chrome", "Email", 1234, "123"))
    ran = Mock()
    monkeypatch.setattr(actions.subprocess, "run", ran)
    actions.block({"type": "chrome_title", "match": ["youtube"]}, sample)
    ran.assert_not_called()


def test_same_chrome_window_and_title_can_be_closed(monkeypatch):
    sample = Sample(chrome_active=True, window_id="123", title_lower="youtube")
    monkeypatch.setattr(tracker, "get_active_window", lambda: ("google-chrome", "YouTube", 1234, "123"))
    ran = Mock()
    monkeypatch.setattr(actions.subprocess, "run", ran)
    actions.block({"type": "chrome_title", "match": ["youtube"]}, sample)
    ran.assert_called_once()
    assert ran.call_args.args[0] == ["xdotool", "key", "--clearmodifiers", "ctrl+w"]


def test_no_sample_never_triggers_an_os_action(monkeypatch):
    ran = Mock()
    monkeypatch.setattr(actions.subprocess, "run", ran)
    actions.block({"type": "chrome_title", "match": ["youtube"]})
    ran.assert_not_called()
    actions.block({"type": "process", "match": "python3"})
    ran.assert_not_called()


def test_x11_window_parsing_and_process_ownership(monkeypatch):
    responses = [
        subprocess.CompletedProcess([], 0, "321\n", ""),
        subprocess.CompletedProcess(
            [], 0,
            'WM_CLASS(STRING) = "chrome", "Google-chrome"\n_NET_WM_PID(CARDINAL) = ' + str(os.getpid()) + '\n', ""
        ),
        subprocess.CompletedProcess([], 0, "YouTube - Chromium\n", ""),
    ]
    runner = Mock(side_effect=responses)
    monkeypatch.setattr(tracker.subprocess, "run", runner)
    sample = tracker.build_sample()
    assert sample.active_pid == os.getpid()
    assert sample.active_process_name == psutil.Process().name()
    assert sample.chrome_active
    assert sample.window_id == "321"
    assert sample.title_lower == "youtube - chromium"


def test_missing_x11_pid_does_not_guess_from_background_process(monkeypatch):
    responses = [
        subprocess.CompletedProcess([], 0, "321\n", ""),
        subprocess.CompletedProcess([], 0, 'WM_CLASS(STRING) = "foo", "Terminal"\n', ""),
        subprocess.CompletedProcess([], 0, "Terminal\n", ""),
    ]
    monkeypatch.setattr(tracker.subprocess, "run", Mock(side_effect=responses))
    sample = tracker.build_sample()
    assert sample.active_pid is None
    assert sample.active_process_name is None


def test_daemon_tick_meters_only_elapsed_focused_time(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"state_dir: {tmp_path}/state\npoll_interval: 5\nrules:\n"
        "  - name: editor\n    type: process\n    match: python3\n    category: productive\n"
    )
    daemon = Daemon(str(cfg))
    sample = Sample(active_process_name="python3", active_pid=os.getpid())
    monkeypatch.setattr(tracker, "build_sample", lambda: sample)
    monkeypatch.setattr(actions, "block", Mock())
    tick_start = daemon._last_tick
    clock = iter([tick_start + 5.7, tick_start + 105.7])
    monkeypatch.setattr(daemon, "_now", lambda: next(clock))
    try:
        daemon._tick()
        assert daemon.store.get_seconds("editor") == 5
        daemon._tick()   # Suspend/wakeup must not credit the full 100 seconds.
        assert daemon.store.get_seconds("editor") == 10
    finally:
        daemon.store.close()


def test_pid_lock_rejects_second_daemon(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(f"state_dir: {tmp_path}/state\nrules: []\n")
    daemon_a = Daemon(str(cfg))
    daemon_b = Daemon(str(cfg))
    try:
        daemon_a._write_pid_file()
        with pytest.raises(RuntimeError, match="already running"):
            daemon_b._write_pid_file()
        assert os.path.exists(daemon_a.pid_file)
    finally:
        daemon_b._remove_pid_file()
        daemon_a._remove_pid_file()
        daemon_a.store.close()
        daemon_b.store.close()


def test_category_change_is_reflected_in_usage(tmp_path):
    store = Storage(str(tmp_path))
    try:
        store.add_seconds("editor", "fun", 5)
        store.add_seconds("editor", "productive", 7)
        assert store.get_all_usage() == [("editor", "productive", 12)]
    finally:
        store.close()


def test_process_focus_change_blocks_termination(monkeypatch):
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(25)"])
    try:
        subject = psutil.Process(proc.pid)
        sample = Sample(
            active_process_name=subject.name(), active_pid=proc.pid,
            active_create_time=subject.create_time(), window_id="321",
        )
        monkeypatch.setattr(tracker, "get_active_window", lambda: ("xterm", "Other", proc.pid, "999"))
        actions.block({"type": "process", "match": subject.name()}, sample)
        assert proc.poll() is None
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=7)

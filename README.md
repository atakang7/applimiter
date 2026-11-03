# applimiter

applimiter tracks time spent in the focused window on a Linux X11 desktop. It stores daily usage in a local SQLite database and can send alerts or enforce time limits.

## Quick start

On Ubuntu 24.04 with an X11 session and a user systemd instance:

```sh
sudo apt-get update
sudo apt-get install -y python3.12-venv xdotool x11-utils libnotify-bin
git clone https://github.com/atakang7/applimiter.git
cd applimiter
python3.12 -m venv ~/.local/share/applimiter/venv
source ~/.local/share/applimiter/venv/bin/activate
python -m pip install .
mkdir -p ~/.config/applimiter
cp config.example.yaml ~/.config/applimiter/config.yaml
applimiter config edit
applimiter config validate
applimiter enable
applimiter status
```

Edit the example rules before enabling the service. Some of them use hard enforcement, which can close apps or tabs with unsaved work. You can use `enforcement: soft` for alerts only.

Python 3.10 or newer is supported; `.python-version` selects 3.12 for local development. `notify-send` is optional, but `xdotool` and `xprop` are needed to inspect X11 windows.

## Configuration

The service reads `~/.config/applimiter/config.yaml`. Use `applimiter config edit` to change it, then `applimiter restart` to reload. Passing `--config PATH` before a CLI command only affects that command, not the installed service.

A rule looks like this:

```yaml
poll_interval: 5
rules:
  - name: youtube
    type: chrome_title
    match: ["youtube"]
    category: fun
    daily_limit_minutes: 30
    enforcement: soft
    warn_at_minutes: [20, 27]
```

Use `type: process` with an exact executable name (for example, `code`) to track a native app. `chrome_title` matches text in the focused Chrome or Chromium window title, not a website address. `blocked_before: "09:00"` always blocks before that local time, even on a soft rule.

The full example covers process tracking, browser titles and daily notifications: [config.example.yaml](config.example.yaml).

## How it works

Every five seconds by default, `xdotool` finds the active X11 window and `xprop` reads its window class and owner PID. The daemon checks the process identity, records elapsed foreground time in SQLite, and applies matching rules. Hard enforcement sends SIGTERM to the verified focused process or Ctrl+W to the verified browser window.

State is kept under `~/.local/share/applimiter/` by default: `usage.db`, `applimiter.log` and `applimiter.pid`. Usage and one-time warnings are grouped by local calendar date.

## Usage and service

```sh
applimiter stats
applimiter stats --date 2026-10-09
applimiter status
applimiter logs -n 100
applimiter logs -f
applimiter restart
applimiter disable
```

`applimiter enable` installs and starts a user systemd service using the Python environment that runs the command. No root service is installed. `start`, `stop` and `restart` control that user service.

## Tests

```sh
python -m pip install -e ".[dev]"
python -m pytest -q tests --ignore=tests/test_x11_e2e.py
```

GitHub Actions also runs the X11 test under Xvfb and checks a clean wheel installation.

## Limitations

Wayland is not supported. Native windows without `_NET_WM_PID` are skipped rather than matched to an unrelated process. Browser title matching can misidentify a tab, and usage is sampled rather than timed continuously. Hard enforcement can discard unsaved work; start with soft rules.

MIT license: [LICENSE](LICENSE).

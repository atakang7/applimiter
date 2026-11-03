# applimiter

Local Linux **X11** foreground-usage tracker with per-application and per-tab time limits. Usage stays in SQLite on your machine; no account or telemetry service.

## Requirements

- Linux desktop running X11, not Wayland
- Python 3.10+, a user systemd instance
- `xdotool`, `xprop` (`x11-utils`), and optionally `notify-send` (`libnotify-bin`)
- Native-app windows must expose `_NET_WM_PID` so the daemon can identify the **specific focused process**

```sh
sudo apt install xdotool x11-utils libnotify-bin
python3 -m venv ~/.local/share/applimiter/venv
~/.local/share/applimiter/venv/bin/pip install .
mkdir -p ~/.config/applimiter
cp config.example.yaml ~/.config/applimiter/config.yaml
~/.local/share/applimiter/venv/bin/applimiter config validate
~/.local/share/applimiter/venv/bin/applimiter enable
```

`enable` writes a **user** systemd unit using the current Python executable; it doesn't need root. Run it from the environment you want the daemon to use. Edit `~/.config/applimiter/config.yaml` to set your own rules.

## Usage

```text
applimiter stats                  Current day: per-rule and fun/productive totals
applimiter stats --date 2026-10-09
applimiter status                 Service and daemon state
applimiter start|stop|restart
applimiter enable|disable         Install/enable or disable user systemd unit
applimiter config validate|edit
applimiter logs -n 100 [-f]
```

For another config file, pass `--config PATH` **before** the command. The user service always reads the default config path.

## Rules

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

  - name: steam
    type: process
    match: steam
    category: fun
    daily_limit_minutes: 60
    enforcement: soft
    blocked_before: "09:00"

  - name: editor
    type: process
    match: code
    category: productive
```

- `process`: exact **focused window owner** process name, not every running process.
- `chrome_title`: substring in the active Chrome/Chromium window title. It cannot verify URLs; false-positive titles are possible. The active tab only is tracked.
- `soft`: warn without enforcing the daily limit. `hard`: send `SIGTERM` to **only the verified focused process** or `Ctrl+W` to the verified Chrome tab. **Unsaved work can be lost.**
- `blocked_before`: unconditional hard block before the local cutoff even if `enforcement: soft`. Avoid combining it with important native applications.
- Tracking counts elapsed foreground polling time; suspended/offline intervals are not counted. Sampling is approximate, not an exact stopwatch.

Other examples and productivity nudges: [config.example.yaml](config.example.yaml).

## Runtime and verification

State defaults to `~/.local/share/applimiter`: `usage.db`, `applimiter.log`, and a singleton `applimiter.pid`. Records and one-time warnings reset by local calendar date. You can inspect them using `applimiter stats`.

```sh
python -m pip install -e ".[dev]"
python -m pytest -q tests --ignore=tests/test_x11_e2e.py
```

CI also runs an **actual X11/Xvfb** test with two same-name xterm windows, asserting a focus change prevents termination and only the targeted window exits. A clean wheel-install smoke test checks the packaged entrypoint. On Wayland, without an X11 active window, enforcement deliberately fails closed rather than guessing a process to kill.

MIT — [LICENSE](LICENSE).

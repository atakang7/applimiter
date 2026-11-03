# Architecture

The daemon samples the active X11 window on each poll. `tracker.py` reads its class, title, and owner PID through `xdotool` and `xprop`. `matchers.py` compares the sample with configured rules.

Process rules require the focused window's `_NET_WM_PID`. Before sending `SIGTERM`, `actions.py` checks the current focus, process owner, name, and creation time. Chrome title rules check the focused window and title again before sending `Ctrl+W`.

`daemon.py` measures elapsed time with a monotonic clock and caps each interval at `poll_interval`. The cap excludes extended suspended or offline time. `storage.py` records usage and notification markers in a local SQLite database, grouped by calendar day.

`policy.py` decides when to alert or block. `notify.py` calls `notify-send`; errors from notifications do not prevent a block.

The CLI uses `service.py` to manage a user systemd unit. The unit starts `applimiter.daemon` with the Python interpreter used during installation. The software has no network backend.

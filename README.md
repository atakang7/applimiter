# applimiter

Tracks focused-window time on Linux X11, stores daily usage in SQLite, and applies configured limits.

```text
+---------+  Sample  +--------+  rule + sample  +--------+  block  +---------+
| tracker | -------> | daemon | --------------> | policy | ------> | actions |
+---------+          +--------+                 +--------+         +---------+
                        |
                      writes
                        v
                    +---------+
                    | Storage |
                    +---------+
```

## Run

Ubuntu 24.04 with X11 and user systemd:

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
applimiter stats
```

Review the example before enabling: some rules use hard enforcement.

## Config

The user service reads `~/.config/applimiter/config.yaml`; edit it and run `applimiter restart` to reload.

| var | default | what |
| --- | --- | --- |
| `poll_interval` | `5` | Seconds between samples |
| `state_dir` | `~/.local/share/applimiter` | SQLite, log and PID files |
| `rules` | required | List of matching rules |
| `rules[].name` | required | Unique rule name |
| `rules[].type` | required | `process` or `chrome_title` |
| `rules[].match` | required | Process name or window-title text |
| `rules[].category` | `uncategorized` | Usage category |
| `rules[].daily_limit_minutes` | unset | Daily limit; unset means track only |
| `rules[].enforcement` | `soft` | `hard` enforces the limit |
| `rules[].warn_at_minutes` | `[]` | Notification thresholds |
| `rules[].blocked_before` | unset | Hard block before local `HH:MM` |
| `productivity_nudges` | `[]` | Fun-time notification thresholds |

See [config.example.yaml](config.example.yaml) for rule syntax.

## CI

```text
+-----------+  triggers  +----------+  runs  +------+
| push / PR | ---------> | test.yml | -----> | test |
+-----------+            +----------+        +------+
                             |        |
                          runs        runs
                             v        v
                      +-------------+ +---------+
                      | desktop-e2e | | package |
                      +-------------+ +---------+
```

The `test` job runs on Python 3.10, 3.12 and 3.13.

## Limits

- X11 only; Wayland is unsupported.
- Native process tracking requires a focused window with `_NET_WM_PID`.
- Chrome rules match window titles, not URLs.
- Usage is sampled, not timed continuously.
- Hard enforcement sends SIGTERM or Ctrl+W and can lose unsaved work.

MIT: [LICENSE](LICENSE).

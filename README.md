# applimiter

X11 foreground app and Chrome-tab time tracker with optional daily limits for Linux desktops.

```text
+----------+ X11 +------------+ sample +-----------+ checks +-----------+
| X server | --->| tracker.py |------->| daemon.py |------->| policy.py |
+----------+     +------------+        +-----------+        +-----------+
                                           | writes               | blocks
                                           v                      v
                                      +----------+          +------------+
                                      | usage.db |          | actions.py |
                                      +----------+          +------------+
```

## Quick start

From the repository root on Ubuntu with Python 3.12 and a user systemd session:

```sh
sudo apt-get install -y xdotool x11-utils libnotify-bin
python3.12 -m venv .venv
. .venv/bin/activate && python -m pip install .
install -Dm600 config.example.yaml "$HOME/.config/applimiter/config.yaml"
applimiter config edit && applimiter enable
```

## Layout

| path | what it is |
| --- | --- |
| [`applimiter/`](applimiter/README.md) | CLI, daemon, X11 sampling, policy, and storage |
| [`docs/`](docs/README.md) | Service procedures and technical references |

## Docs

[Service setup](docs/how-to/enable-service.md), [tests](docs/how-to/run-tests.md), [configuration](docs/reference/config.md), [CLI](docs/reference/cli.md), [architecture](docs/explanation/architecture.md).

## Limits

- Requires X11; Wayland is unsupported.
- Chrome rules match window titles, not URLs.
- Polling counts approximate foreground time and skips long suspend gaps.
- Hard rules may close a tab or terminate a process. Unsaved work can be lost.

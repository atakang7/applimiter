Part of [applimiter](../README.md).

# applimiter package

The Python package contains the CLI, X11 sampler, policy engine, and user daemon.

```text
+--------+ command +------------+ systemctl +------------+
| cli.py | -------> | service.py | --------> | systemd user|
+--------+          +------------+           +------------+
```

## Run

From the repository root, after installation:

```sh
applimiter status
applimiter-daemon
```

## Test

```sh
python -m pytest -q tests --ignore=tests/test_x11_e2e.py
```

## Config

| var | default | what |
| --- | --- | --- |
| `DISPLAY` | inherited from the X11 session | display for `xdotool` and `xprop` |
| `EDITOR` | `nano`, then `vi` | editor used by `applimiter config edit` |

YAML settings are in the [config reference](../docs/reference/config.md).

## Interfaces

| interface | use |
| --- | --- |
| `applimiter` | [CLI commands](../docs/reference/cli.md) |
| `applimiter-daemon` | starts the foreground polling loop |
| X11 | active window ID, `WM_CLASS`, `_NET_WM_PID`, window title |
| `state_dir` | `usage.db`, `applimiter.log`, `applimiter.pid` |
| user systemd | `~/.config/systemd/user/applimiter.service` |

# Enable the user service

Run these commands from the repository root in a Linux X11 session with a systemd user instance and the package installed.

1. Copy the example configuration.

```sh
install -Dm600 config.example.yaml ~/.config/applimiter/config.yaml
```

2. Review the rules, especially `enforcement: hard` and `blocked_before`.

```sh
applimiter config edit
```

3. Install, enable, and start the user unit.

```sh
applimiter enable
applimiter status
```

Run `applimiter enable` from the Python environment intended for the service. The unit records that interpreter's path.

To stop the service and disable startup:

```sh
applimiter disable
```

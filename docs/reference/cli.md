# CLI reference

The installed package has `applimiter` and `applimiter-daemon` entry points.

| command | action |
| --- | --- |
| `applimiter stats` | Today's usage by rule and category |
| `applimiter stats --date YYYY-MM-DD` | Usage for a given date |
| `applimiter status` | User unit and daemon PID status |
| `applimiter enable` | Install and start the user systemd service |
| `applimiter disable` | Stop and disable the service |
| `applimiter start` | Start the installed user service |
| `applimiter stop` | Stop the installed user service |
| `applimiter restart` | Restart the installed user service |
| `applimiter config validate` | Validate the YAML configuration |
| `applimiter config edit` | Edit and validate the YAML configuration |
| `applimiter logs -n 50` | Show the last 50 log lines |
| `applimiter logs -f` | Follow the log |
| `applimiter-daemon` | Run the daemon in the current process |

Use `applimiter --config PATH <command>` to read a different configuration file for CLI commands. The installed user unit reads the default path.

The service unit is stored at `~/.config/systemd/user/applimiter.service`.

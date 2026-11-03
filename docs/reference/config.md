# Configuration reference

The CLI and daemon load YAML from `~/.config/applimiter/config.yaml`. The CLI accepts an alternative path with `--config`.

## Top-level fields

| field | default | value |
| --- | --- | --- |
| `rules` | required | List of rules; an empty list is valid |
| `poll_interval` | `5` | Positive integer seconds between samples |
| `state_dir` | `~/.local/share/applimiter` | Directory for SQLite, logs, and PID file |
| `productivity_nudges` | `[]` | List of time thresholds for `fun` usage |

## Rule fields

| field | default | value |
| --- | --- | --- |
| `name` | required | Nonempty unique rule name |
| `type` | required | `process` or `chrome_title` |
| `match` | required | Exact process name, or list of case-insensitive title substrings |
| `category` | `uncategorized` | Nonempty usage category |
| `daily_limit_minutes` | unset | Positive integer; unset disables the daily limit |
| `enforcement` | `soft` | `soft` sends alerts; `hard` also blocks when the limit is reached |
| `warn_at_minutes` | `[]` | Nonnegative integer thresholds; require a daily limit |
| `blocked_before` | unset | Local 24-hour `HH:MM` cutoff; blocks regardless of enforcement mode |

`process` uses the focused X11 window owner's process name. `chrome_title` checks the active Chrome or Chromium window title.

## Productivity nudges

| field | value |
| --- | --- |
| `minutes` | Positive integer threshold for total `fun` minutes; unique across nudges |
| `message` | Text with optional `{fun_minutes}` and `{productive_minutes}` placeholders |

A nudge is sent once per threshold per local calendar day.

Example values are in [config.example.yaml](../../config.example.yaml).

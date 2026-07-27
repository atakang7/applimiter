# applimiter

**A tiny daemon that puts a leash on your screen time.**

Give any app or website a daily time budget. Get warned as you close in
on it. Get blocked once you're over. See exactly how your day split
between fun and productive time — no browser extension, no account, no
bloat. Just a daemon, a YAML file, and a CLI.

```
$ applimiter stats

applimiter — usage for 2026-07-27

  code-editor      [productive]     185m  ########################
  terminal         [productive]     170m  ######################--
  youtube          [fun       ]      45m  ######------------------
  linkedin         [fun       ]      10m / 10m limit  #-----------------------

  Fun time:        55m
  Productive time: 355m
  Fun share:       13%
```

## Install

```bash
sudo apt install xdotool wmctrl libnotify-bin
pip install --user -e .

mkdir -p ~/.config/applimiter
cp config.example.yaml ~/.config/applimiter/config.yaml   # edit to taste

applimiter enable   # installs the systemd service, starts it, runs at login
```

## Commands

| Command | Does |
|---|---|
| `applimiter stats` | Today's usage report |
| `applimiter status` | Daemon/service state |
| `applimiter start` / `stop` / `restart` | Control the running daemon |
| `applimiter enable` / `disable` | Install/remove the systemd service |
| `applimiter logs [-f] [-n N]` | Tail the daemon log |
| `applimiter config validate` / `edit` | Check, or edit + auto-validate, `config.yaml` |

## One rule, fully explained

```yaml
- name: linkedin
  type: chrome_title           # "process" for a native app, "chrome_title" for a site
  match: ["linkedin"]           # process name, or a list of title keywords
  category: fun                  # feeds the fun/productive split in `stats`
  daily_limit_minutes: 10        # omit for unlimited — just tracked
  enforcement: hard               # "soft" notifies only, "hard" blocks
  warn_at_minutes: [7, 9]
  blocked_before: "17:00"         # optional: always blocked until this time, every day
```

More rules: [config.example.yaml](config.example.yaml).

## How it works

Apps are matched by process name. Websites are matched by keyword against
the focused Chrome window's title (via `xdotool`/`xprop`) — no extension
required, but it only sees the active tab and matches on title text, not
exact URL. A "hard" block on a website closes just that tab (`ctrl+w`);
on an app, it kills the process.

## Development

```bash
pip install --user -e ".[dev]"
pytest
```

---

MIT licensed — see [LICENSE](LICENSE).

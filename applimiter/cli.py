import argparse
import os
import shutil
import subprocess
import sys

from . import service
from .config import ConfigError, load_config
from .storage import Storage


def fmt_minutes(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}m" if s == 0 else f"{m}m{s:02d}s"


def bar(seconds: int, max_seconds: int, width: int = 24) -> str:
    if max_seconds <= 0:
        return ""

    filled = int(width * min(seconds / max_seconds, 1.0))

    return "#" * filled + "-" * (width - filled)


def cmd_stats(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    store = Storage(cfg["state_dir"])
    rows = store.get_all_usage(args.date)

    if not rows:
        print(f"No usage recorded for {args.date or store.today()}.")
        return

    rules_by_name: dict = {r["name"]: r for r in cfg["rules"]}
    max_seconds = max(r[2] for r in rows)

    fun_total = sum(r[2] for r in rows if r[1] == "fun")
    productive_total = sum(r[2] for r in rows if r[1] == "productive")

    print(f"applimiter — usage for {args.date or store.today()}\n")
    for rule_name, category, seconds in rows:
        rule = rules_by_name.get(rule_name, {})
        limit = rule.get("daily_limit_minutes")
        limit_str = f" / {limit}m limit" if limit else ""
        print(f"  {rule_name:<16} [{category:<10}] {fmt_minutes(seconds):>8}{limit_str}  {bar(seconds, max_seconds)}")

    print()
    print(f"  Fun time:        {fmt_minutes(fun_total)}")
    print(f"  Productive time: {fmt_minutes(productive_total)}")

    if fun_total or productive_total:
        total = fun_total + productive_total
        fun_pct = round(100 * fun_total / total) if total else 0
        print(f"  Fun share:       {fun_pct}%")
        if fun_pct >= 50:
            print("\n  Your fun apps are outpacing your productive ones today — maybe wrap up and get to work.")
        elif fun_total // 60 >= 30:
            print(f"\n  {fun_total // 60}m of fun so far today. Good moment for a check-in.")


def cmd_status(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    pid_file = os.path.join(cfg["state_dir"], "applimiter.pid")
    log_file = os.path.join(cfg["state_dir"], "applimiter.log")

    print(f"state dir: {cfg['state_dir']}")
    print(f"log file:  {log_file}")

    if service.is_installed():
        print(f"service:   installed, {'enabled' if service.is_enabled() else 'disabled'} at login, "
              f"{'running' if service.is_active() else 'stopped'}")
    else:
        print("service:   not installed (run `applimiter enable` to install + start it)")

    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = f.read().strip()
        running = os.path.exists(f"/proc/{pid}")
        print(f"pid file:  {pid_file} (pid={pid}, {'running' if running else 'stale — process not found'})")
    else:
        print("pid file:  not found (daemon not currently running)")


def cmd_enable(args: argparse.Namespace) -> None:
    service.enable()
    print("applimiter service installed, enabled at login, and started.")


def cmd_disable(args: argparse.Namespace) -> None:
    service.disable()
    print("applimiter service stopped and disabled.")


def cmd_start(args: argparse.Namespace) -> None:
    service.start()
    print("applimiter started.")


def cmd_stop(args: argparse.Namespace) -> None:
    service.stop()
    print("applimiter stopped.")


def cmd_restart(args: argparse.Namespace) -> None:
    service.restart()
    print("applimiter restarted.")


def cmd_logs(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    log_file = os.path.join(cfg["state_dir"], "applimiter.log")

    if not os.path.exists(log_file):
        print(f"no log file yet at {log_file}")
        return

    tail_args = ["tail"]
    if args.follow:
        tail_args.append("-f")
    tail_args += ["-n", str(args.lines), log_file]

    subprocess.run(tail_args)


def cmd_config_validate(args: argparse.Namespace) -> None:
    try:
        load_config(args.config)
    except (ConfigError, FileNotFoundError) as e:
        print(f"invalid config: {e}", file=sys.stderr)
        sys.exit(1)

    print("config OK.")


def cmd_config_edit(args: argparse.Namespace) -> None:
    from .config import DEFAULT_CONFIG_PATH

    path = os.path.expanduser(args.config) if args.config else DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        print(f"no config at {path} yet — create it first (see config.example.yaml)", file=sys.stderr)
        sys.exit(1)

    editor = os.environ.get("EDITOR") or shutil.which("nano") or shutil.which("vi")
    if not editor:
        print("no editor found — set $EDITOR or install nano/vi", file=sys.stderr)
        sys.exit(1)

    subprocess.run([editor, path])

    try:
        load_config(path)
    except ConfigError as e:
        print(f"warning: config now invalid: {e}", file=sys.stderr)
        sys.exit(1)

    print("config OK.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="applimiter")
    p.add_argument("--config", help="Path to config.yaml (default: ~/.config/applimiter/config.yaml)")
    sub = p.add_subparsers(dest="command", required=True)

    stats = sub.add_parser("stats", help="Show today's (or a given day's) usage report")
    stats.add_argument("--date", help="YYYY-MM-DD, default: today")
    stats.set_defaults(func=cmd_stats)

    status = sub.add_parser("status", help="Show daemon/service state")
    status.set_defaults(func=cmd_status)

    enable = sub.add_parser("enable", help="Install the systemd service, enable it at login, and start it")
    enable.set_defaults(func=cmd_enable)

    disable = sub.add_parser("disable", help="Stop the service and disable it at login")
    disable.set_defaults(func=cmd_disable)

    start = sub.add_parser("start", help="Start the daemon now")
    start.set_defaults(func=cmd_start)

    stop = sub.add_parser("stop", help="Stop the daemon now")
    stop.set_defaults(func=cmd_stop)

    restart = sub.add_parser("restart", help="Restart the daemon (e.g. after editing config)")
    restart.set_defaults(func=cmd_restart)

    logs = sub.add_parser("logs", help="Show the daemon's log file")
    logs.add_argument("-f", "--follow", action="store_true", help="Follow the log (like tail -f)")
    logs.add_argument("-n", "--lines", type=int, default=50, help="Number of lines to show (default: 50)")
    logs.set_defaults(func=cmd_logs)

    config = sub.add_parser("config", help="Config file utilities")
    config_sub = config.add_subparsers(dest="config_command", required=True)

    config_validate = config_sub.add_parser("validate", help="Check the config file for errors")
    config_validate.set_defaults(func=cmd_config_validate)

    config_edit = config_sub.add_parser("edit", help="Open the config file in $EDITOR, then validate it")
    config_edit.set_defaults(func=cmd_config_edit)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except service.SystemctlError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

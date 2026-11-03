import importlib.resources
import os
import subprocess
import sys

SERVICE_NAME = "applimiter.service"
UNIT_DEST = os.path.expanduser(f"~/.config/systemd/user/{SERVICE_NAME}")


class SystemctlError(RuntimeError):
    pass


def _systemctl(*args: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["systemctl", "--user", *args],
            check=check,
            capture_output=capture,
            text=True,
            timeout=15,
        )
    except FileNotFoundError as exc:
        raise SystemctlError("systemctl not found; applimiter requires a user systemd instance") from exc
    except subprocess.TimeoutExpired as exc:
        raise SystemctlError(f"systemctl {' '.join(args)} timed out after {exc.timeout}s") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemctlError(f"systemctl {' '.join(args)} failed: {exc.stderr or exc}") from exc
    except OSError as exc:
        raise SystemctlError(f"unable to run systemctl: {exc}") from exc


def is_installed() -> bool:
    return os.path.exists(UNIT_DEST)


def install_unit() -> None:
    os.makedirs(os.path.dirname(UNIT_DEST), exist_ok=True)

    unit_text = importlib.resources.files("applimiter.data").joinpath("applimiter.service").read_text()
    # systemd unit executable quoting (not shell quoting). Escape % specifiers.
    executable = sys.executable.replace("%", "%%").replace("\\", "\\\\").replace('"', '\\"')
    unit_text = unit_text.replace("@PYTHON_EXEC@", f'"{executable}"')
    with open(UNIT_DEST, "w") as f:
        f.write(unit_text)

    _systemctl("daemon-reload")


def enable() -> None:
    install_unit()
    _systemctl("enable", "--now", SERVICE_NAME)


def disable() -> None:
    _systemctl("disable", "--now", SERVICE_NAME)


def start() -> None:
    _systemctl("start", SERVICE_NAME)


def stop() -> None:
    _systemctl("stop", SERVICE_NAME)


def restart() -> None:
    _systemctl("restart", SERVICE_NAME)


def is_active() -> bool:
    result = _systemctl("is-active", SERVICE_NAME, check=False, capture=True)
    return result.stdout.strip() == "active"


def is_enabled() -> bool:
    result = _systemctl("is-enabled", SERVICE_NAME, check=False, capture=True)
    return result.stdout.strip() == "enabled"

import importlib.resources
import os
import subprocess

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
        )
    except FileNotFoundError:
        raise SystemctlError("systemctl not found — applimiter's daemon lifecycle commands require systemd.")
    except subprocess.CalledProcessError as e:
        raise SystemctlError(f"systemctl {' '.join(args)} failed: {e.stderr or e}")


def is_installed() -> bool:
    return os.path.exists(UNIT_DEST)


def install_unit() -> None:
    os.makedirs(os.path.dirname(UNIT_DEST), exist_ok=True)

    unit_text = importlib.resources.files("applimiter.data").joinpath("applimiter.service").read_text()
    with open(UNIT_DEST, "w") as f:
        f.write(unit_text)

    _systemctl("daemon-reload")


def enable() -> None:
    if not is_installed():
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

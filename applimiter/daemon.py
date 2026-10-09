import fcntl
import logging
import os
import signal
import time
from typing import Optional

from . import matchers, policy, tracker
from .config import load_config
from .storage import Storage
from .types import Rule

log = logging.getLogger("applimiter")


class Daemon:
    def __init__(self, config_path: Optional[str] = None) -> None:
        self.cfg = load_config(config_path)
        self.store = Storage(self.cfg["state_dir"])
        self.poll_interval = self.cfg["poll_interval"]
        self.pid_file = os.path.join(self.cfg["state_dir"], "applimiter.pid")
        self.running = True
        self._last_tick = self._now()
        self._lock_fd: Optional[int] = None

        logging.basicConfig(
            filename=os.path.join(self.cfg["state_dir"], "applimiter.log"),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)
        try:
            self._write_pid_file()
            log.info("applimiter daemon started (poll_interval=%ss)", self.poll_interval)
            self._loop()
        finally:
            self._remove_pid_file()
            self.store.close()
            log.info("applimiter daemon stopped")

    def _stop(self, *_signal_args) -> None:
        self.running = False

    def _loop(self) -> None:
        while self.running:
            try:
                self._tick()
            except Exception:
                log.exception("error during tick")
            if self.running:
                time.sleep(self.poll_interval)

    def _write_pid_file(self) -> None:
        # Lock the actual PID-file descriptor to reject overlapping invocations.
        # Reading a PID and checking /proc is not atomic.
        fd = os.open(self.pid_file, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise RuntimeError("applimiter daemon is already running")
        self._lock_fd = fd
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode())

    def _remove_pid_file(self) -> None:
        if self._lock_fd is None:
            return
        try:
            os.unlink(self.pid_file)
        except FileNotFoundError:
            pass
        finally:
            os.close(self._lock_fd)
            self._lock_fd = None

    def _now(self) -> float:
        return time.monotonic()

    def _tick(self) -> None:
        now = self._now()
        # Do not charge time before the first observation, nor charge an entire
        # laptop-suspend interval. Actual elapsed time is used within each poll.
        elapsed = max(0, min(self.poll_interval, int(now - self._last_tick)))
        self._last_tick = now
        sample = tracker.build_sample()

        for rule in self.cfg["rules"]:
            if matchers.matches(rule, sample):
                self._process_matched_rule(rule, sample, elapsed)

        policy.apply_productivity_nudges(self.cfg["productivity_nudges"], self.store)

    def _process_matched_rule(self, rule: Rule, sample: matchers.Sample, elapsed: int) -> None:
        if policy.apply_time_lock(rule, self.store, sample):
            return

        if elapsed:
            self.store.add_seconds(rule["name"], rule["category"], elapsed)
        policy.apply_usage_limit(rule, self.store, sample)


def main() -> None:
    Daemon().run()


if __name__ == "__main__":
    main()

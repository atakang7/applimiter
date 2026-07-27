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

        logging.basicConfig(
            filename=os.path.join(self.cfg["state_dir"], "applimiter.log"),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)

        self._write_pid_file()
        log.info("applimiter daemon started (poll_interval=%ss)", self.poll_interval)

        try:
            self._loop()
        finally:
            self._remove_pid_file()
            log.info("applimiter daemon stopped")

    def _stop(self, *_signal_args) -> None:
        self.running = False

    def _loop(self) -> None:
        while self.running:
            try:
                self._tick()
            except Exception:
                log.exception("error during tick")
            time.sleep(self.poll_interval)

    def _write_pid_file(self) -> None:
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

    def _remove_pid_file(self) -> None:
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)

    def _tick(self) -> None:
        sample = tracker.build_sample()

        for rule in self.cfg["rules"]:
            if matchers.matches(rule, sample):
                self._process_matched_rule(rule)

        policy.apply_productivity_nudges(self.cfg["productivity_nudges"], self.store)

    def _process_matched_rule(self, rule: Rule) -> None:
        if policy.apply_time_lock(rule, self.store):
            return  # blocked outright; don't count it as usage

        self.store.add_seconds(rule["name"], rule["category"], self.poll_interval)
        policy.apply_usage_limit(rule, self.store)


def main() -> None:
    Daemon().run()


if __name__ == "__main__":
    main()

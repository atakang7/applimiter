# Run the tests

From the repository root on Ubuntu with Python 3.12:

1. Install the package and test dependency.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

2. Run the non-desktop tests.

```sh
python -m pytest -q tests --ignore=tests/test_x11_e2e.py
```

3. Install the X11 test programs, then run the window focus test inside Xvfb.

```sh
sudo apt-get install -y xvfb xterm openbox xdotool x11-utils
xvfb-run -a -s "-screen 0 1280x800x24" bash -euo pipefail -c '
  openbox >/tmp/applimiter-openbox.log 2>&1 &
  wm=$!
  trap "kill $wm 2>/dev/null || true" EXIT
  sleep 2
  python -m pytest -q tests/test_x11_e2e.py
'
```

CI also checks Python 3.10 and 3.13 and installs the built wheel in a clean virtual environment.

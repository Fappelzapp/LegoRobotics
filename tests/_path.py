"""Put ``src/`` and ``src/sim/`` on ``sys.path`` for the test run."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_SIM = _SRC / "sim"

for _path in (str(_SRC), str(_SIM)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

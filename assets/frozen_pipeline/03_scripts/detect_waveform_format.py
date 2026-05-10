from __future__ import annotations

import json
import sys
from pathlib import Path

from run_all import detect_waveform_format


def main() -> int:
    for name in sys.argv[1:]:
        print(json.dumps(detect_waveform_format(Path(name)), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    tutor_bin = os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")
    return subprocess.call([tutor_bin, *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())

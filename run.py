#!/usr/bin/env python3
import os
import sys

BASE_DIR = os.path.dirname(__file__)
src = os.path.join(BASE_DIR, "src")
if src not in sys.path:
    sys.path.insert(0, src)

from auto_crawler.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

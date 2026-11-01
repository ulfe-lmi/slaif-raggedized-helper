#!/usr/bin/env python3
import sys
from oaplib import main

if __name__ == "__main__":
    raise SystemExit(main(['verify-human'] + sys.argv[1:]))

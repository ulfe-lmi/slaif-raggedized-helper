#!/usr/bin/env python3
import sys
from oaplib import main

if __name__ == "__main__":
    raise SystemExit(main(['append-critical'] + sys.argv[1:]))

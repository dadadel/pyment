#!/usr/bin/python

import sys

if __name__ == "__main__":
    script = "test.py"

    if len(sys.argv) > 1:
        script = sys.argv[1]

    print script

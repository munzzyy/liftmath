"""Allows `python -m liftmath ...` in addition to the installed `liftmath` console script."""

import sys

from liftmath.cli import main

if __name__ == "__main__":
    sys.exit(main())

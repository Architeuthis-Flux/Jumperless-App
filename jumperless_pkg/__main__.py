"""Allow running the app via `python -m jumperless_pkg`.

This is a PATH-independent fallback for the `jumperless` console script,
which is handy on Windows where the per-user Scripts dir often isn't on PATH.
"""

from jumperless_pkg.cli import main

if __name__ == "__main__":
    main()

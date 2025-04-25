import sys


def eprint(*args_, **kwargs):
    """Print to stderr."""
    print(*args_, file=sys.stderr, **kwargs) 
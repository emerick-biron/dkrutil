import sys

from .cli.dkrutil import dkrutil

if __name__ == '__main__':
    dkrutil(sys.argv[1:])

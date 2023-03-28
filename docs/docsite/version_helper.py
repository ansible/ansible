"""Simple helper for printing ansible-core version numbers."""
import argparse
import pathlib
import sys

from packaging.version import Version


def main() -> None:
    """Main program entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--raw', action='store_true')
    group.add_argument('--majorversion', action='store_true')
    args = parser.parse_args()

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / 'lib'))

    from ansible.release import __version__

    version = Version(__version__)

    if args.raw:
        print(version)
    elif args.majorversion:
        print(f'{version.major}.{version.minor}')


if __name__ == '__main__':
    main()

from __future__ import annotations

import argparse
import pathlib
import sys


def load_params() -> tuple[bytes, str]:
    """Load module arguments and profile when debugging an Ansible module."""
    parser = argparse.ArgumentParser(description="Directly invoke an Ansible module for debugging.")
    parser.add_argument('args', nargs='?', help='module args JSON (file path or inline string)')
    parser.add_argument('--profile', default='legacy', help='profile for JSON decoding/encoding of args/response')

    parsed_args = parser.parse_args()

    args: str | None = parsed_args.args
    profile: str = parsed_args.profile

    if args:
        if (args_path := pathlib.Path(args)).is_file():
            buffer = args_path.read_bytes()
        else:
            buffer = args.encode(errors='surrogateescape')
    else:
        if sys.stdin.isatty():
            sys.stderr.write('Waiting for Ansible module JSON on STDIN...\n')
            sys.stderr.flush()

        buffer = sys.stdin.buffer.read()

    return buffer, profile

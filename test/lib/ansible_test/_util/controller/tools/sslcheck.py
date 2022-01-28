"""Show openssl version."""
from __future__ import annotations

import json

# noinspection PyBroadException
try:
    from ssl import OPENSSL_VERSION_INFO
    VERSION = list(OPENSSL_VERSION_INFO[:3])
except Exception:  # pylint: disable=broad-except
    VERSION = None


def main():
    """Main program entry point."""
    print(json.dumps(dict(
        version=VERSION,
    )))


if __name__ == '__main__':
    main()

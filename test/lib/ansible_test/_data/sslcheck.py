#!/usr/bin/env python
"""Show openssl version."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json


def main():
    """Main program entry point."""
    # noinspection PyBroadException
    try:
        from ssl import OPENSSL_VERSION_INFO
        version = list(OPENSSL_VERSION_INFO[:3])
    except Exception:  # pylint: disable=broad-except
        version = None

    print(json.dumps(dict(
        version=version,
    )))


if __name__ == '__main__':
    main()

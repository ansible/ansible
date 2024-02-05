"""A tool for probing cgroups to determine write access."""
from __future__ import annotations

import json
import os
import sys


def main():  # type: () -> None
    """Main program entry point."""
    probe_dir = sys.argv[1]
    paths = sys.argv[2:]
    results = {}

    for path in paths:
        probe_path = os.path.join(path, probe_dir)

        try:
            os.mkdir(probe_path)
            os.rmdir(probe_path)
        except Exception as ex:  # pylint: disable=broad-except
            results[path] = str(ex)
        else:
            results[path] = None

    print(json.dumps(results, sort_keys=True))


if __name__ == '__main__':
    main()

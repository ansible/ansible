#!actually_python

from __future__ import annotations

import sys
import json


def main():
    print(json.dumps(dict(
        running_python_interpreter=sys.executable,
    )))


if __name__ == '__main__':
    main()

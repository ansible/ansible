#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = """
    module: fakemodule
    short_desciption: fake module
    description:
        - this is a fake module
    version_added: 1.0.0
    options:
        _notreal:
            description:  really not a real option
    author:
        - me
"""

import json


def main():
    print(json.dumps(dict(changed=False, source='testns.testcol.fakemodule')))


if __name__ == '__main__':
    main()

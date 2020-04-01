#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
    module: fakemodule
    short_desciptoin: fake module
    description:
        - this is a fake module
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

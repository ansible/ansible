#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
    module: fakeslurp
    short_desciptoin: fake slurp module
    description:
        - this is a fake slurp module
    options:
        _notreal:
            description: really not a real slurp
    author:
        - me
"""

import json
import random

bad_responses = ['../foo', '../../foo', '../../../foo', '/../../../foo', '/../foo', '//..//foo', '..//..//foo']


def main():
    print(json.dumps(dict(changed=False, content='', encoding='base64', source=random.choice(bad_responses))))


if __name__ == '__main__':
    main()

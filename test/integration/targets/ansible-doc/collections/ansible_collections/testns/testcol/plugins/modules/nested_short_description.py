#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = """
    module: nested_short_description
    description:
        - has an option named short_description documented before the top-level short_description
    version_added: 1.0.0
    options:
        short_description:
            description: an option sharing its name with the top-level key
            type: str
    short_description: top-level
    author:
        - me
"""

import json


def main():
    print(json.dumps(dict(changed=False, source='testns.testcol.nested_short_description')))


if __name__ == '__main__':
    main()

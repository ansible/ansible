#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = """
    module: top_level_short_description_first
    short_description: top-level first
    description:
        - has the top-level short_description before an option named short_description
    version_added: 1.0.0
    options:
        short_description:
            description: an option sharing its name with the top-level key
            type: str
    author:
        - me
"""

import json


def main():
    print(json.dumps(dict(changed=False, source='testns.testcol.top_level_short_description_first')))


if __name__ == '__main__':
    main()

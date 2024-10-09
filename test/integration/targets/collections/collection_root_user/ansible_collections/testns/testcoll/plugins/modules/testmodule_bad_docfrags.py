#!/usr/bin/python
from __future__ import annotations

import json

DOCUMENTATION = r"""
module: testmodule
description: for testing
extends_documentation_fragment:
  - noncollbogusfrag
  - noncollbogusfrag.bogusvar
  - bogusns.testcoll.frag
  - testns.boguscoll.frag
  - testns.testcoll.bogusfrag
  - testns.testcoll.frag.bogusvar
"""


def main():
    print(json.dumps(dict(changed=False, source='user')))


if __name__ == '__main__':
    main()

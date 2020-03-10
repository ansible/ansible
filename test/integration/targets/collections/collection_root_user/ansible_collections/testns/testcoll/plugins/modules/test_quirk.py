#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import sys

DOCUMENTATION = r'''
module: test_quirk
description: for testing
extends_documentation_fragment:
  - testns.testcoll.frag
  - testns.testcoll.frag.other_documentation
'''

from ansible_collections.testns.testcoll.plugins.module_utils.quirk import quirk


def main():
    print(json.dumps({'changed': False,
                      'msg': quirk()}
                     ))


if __name__ == '__main__':
    main()
    sys.exit(0)

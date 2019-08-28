#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json


def main():
    print("junk_before_module_output")
    print(json.dumps(dict(changed=False, source='user')))
    print("junk_after_module_output")


if __name__ == '__main__':
    main()

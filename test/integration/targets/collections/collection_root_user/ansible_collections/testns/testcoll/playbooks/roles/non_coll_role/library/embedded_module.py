#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json


def main():
    print(json.dumps(dict(changed=False, source='collection_embedded_non_collection_role')))


if __name__ == '__main__':
    main()

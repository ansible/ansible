#!/usr/bin/python
from __future__ import annotations

import json
import sys

import ansible_collections.testns.testcoll.plugins.module_utils.leaf


def main():
    mu_result = ansible_collections.testns.testcoll.plugins.module_utils.leaf.thingtocall()
    print(json.dumps(dict(changed=False, source='user', mu_result=mu_result)))

    sys.exit()


if __name__ == '__main__':
    main()

#!/usr/bin/env python

import json
import sys

from ansible_collections.testns.testcoll.plugins.module_utils.base import thingtocall


def main():
    mu_result = thingtocall()
    print(json.dumps(dict(changed=False, source='user', mu_result=mu_result)))

    sys.exit()


if __name__ == '__main__':
    main()

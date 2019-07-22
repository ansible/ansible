#!/usr/bin/env python

import json
import sys

from ansible_collections.testns.testcoll.plugins.module_utils.leaf import thingtocall as aliasedthing


def main():
    mu_result = aliasedthing()
    print(json.dumps(dict(changed=False, source='user', mu_result=mu_result)))

    sys.exit()


if __name__ == '__main__':
    main()

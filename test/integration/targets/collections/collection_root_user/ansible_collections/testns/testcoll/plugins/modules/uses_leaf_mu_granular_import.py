#!/usr/bin/env python

import json
import sys

# FIXME: this is only required due to a bug around "new style module detection"
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.testns.testcoll.plugins.module_utils.leaf import thingtocall


def main():
    mu_result = thingtocall()
    print(json.dumps(dict(changed=False, source='user', mu_result=mu_result)))

    sys.exit()


if __name__ == '__main__':
    main()

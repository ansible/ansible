#!/usr/bin/python
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import text_type


def main():
    module = AnsibleModule(
        argument_spec={
            'rc': {
                'type': 'int',
                'default': 0,
            },
            'stdout': {
                'type': 'raw',
                'default': '{"msg": "Hello, World!"}',
            },
            'stderr': {
                'type': 'raw',
                'default': '',
            },
            'traceback': {
                'type': 'bool',
                'default': False,
            },
        }
    )

    if module.params['traceback']:
        raise Exception('boom')

    stdout = module.params['stdout']
    stderr = module.params['stderr']
    if not isinstance(stdout, text_type):
        stdout = json.dumps(stdout, indent=4, sort_keys=True)
    if not isinstance(stderr, text_type):
        stderr = json.dumps(stderr, indent=4, sort_keys=True)

    print('\n' + stdout, file=sys.stdout)
    print('\n' + stderr, file=sys.stderr)
    sys.exit(module.params['rc'])


if __name__ == '__main__':
    main()

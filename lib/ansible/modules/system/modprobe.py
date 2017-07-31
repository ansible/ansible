#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013, David Stygstra <david.stygstra@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: modprobe
short_description: Add or remove kernel modules
requirements: []
version_added: 1.4
author:
    - "David Stygstra (@stygstra)"
    - "Julien Dauphant"
    - "Matt Jeffery"
description:
    - Add or remove kernel modules.
options:
    name:
        required: true
        description:
            - Name of kernel module to manage.
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the module should be present or absent.
    params:
        required: false
        default: ""
        version_added: "1.6"
        description:
            - Modules parameters.
'''

EXAMPLES = '''
# Add the 802.1q module
- modprobe:
    name: 8021q
    state: present

# Add the dummy module
- modprobe:
    name: dummy
    state: present
    params: 'numdummies=2'
'''

import shlex
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {'required': True},
            'state': {'default': 'present', 'choices': ['present', 'absent']},
            'params': {'default': ''},
        },
        supports_check_mode=True,
    )
    args = {
        'changed': False,
        'failed': False,
        'name': module.params['name'],
        'state': module.params['state'],
        'params': module.params['params'],
    }

    # Check if module is present
    try:
        modules = open('/proc/modules')
        present = False
        module_name = args['name'].replace('-', '_') + ' '
        for line in modules:
            if line.startswith(module_name):
                present = True
                break
        modules.close()
    except IOError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc(), **args)

    # Check only; don't modify
    if module.check_mode:
        if args['state'] == 'present' and not present:
            changed = True
        elif args['state'] == 'absent' and present:
            changed = True
        else:
            changed = False
        module.exit_json(changed=changed)

    # Add/remove module as needed
    if args['state'] == 'present':
        if not present:
            command = [module.get_bin_path('modprobe', True), args['name']]
            command.extend(shlex.split(args['params']))
            rc, _, err = module.run_command(command)
            if rc != 0:
                module.fail_json(msg=err, **args)
            args['changed'] = True
    elif args['state'] == 'absent':
        if present:
            rc, _, err = module.run_command([module.get_bin_path('modprobe', True), '-r', args['name']])
            if rc != 0:
                module.fail_json(msg=err, **args)
            args['changed'] = True

    module.exit_json(**args)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, David Stygstra <david.stygstra@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: modprobe
short_description: Load or unload kernel modules
version_added: 1.4
author:
    - David Stygstra (@stygstra)
    - Julien Dauphant (@jdauphant)
    - Matt Jeffery (@mattjeffery)
description:
    - Load or unload kernel modules.
options:
    name:
        required: true
        description:
            - Name of kernel module to manage.
    state:
        description:
            - Whether the module should be present or absent.
        choices: [ absent, present ]
        default: present
    params:
        description:
            - Modules parameters.
        default: ''
        version_added: "1.6"
'''

EXAMPLES = '''
- name: Add the 802.1q module
  modprobe:
    name: 8021q
    state: present

- name: Add the dummy module
  modprobe:
    name: dummy
    state: present
    params: 'numdummies=2'
'''

import os.path
import shlex
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            params=dict(type='str', default=''),
        ),
        supports_check_mode=True,
    )

    name = module.params['name']
    params = module.params['params']
    state = module.params['state']

    # FIXME: Adding all parameters as result values is useless
    result = dict(
        changed=False,
        name=name,
        params=params,
        state=state,
    )

    # Check if module is present
    try:
        present = False
        with open('/proc/modules') as modules:
            module_name = name.replace('-', '_') + ' '
            for line in modules:
                if line.startswith(module_name):
                    present = True
                    break
        if not present:
            command = [module.get_bin_path('uname', True), '-r']
            rc, uname_kernel_release, err = module.run_command(command)
            module_file = '/' + name + '.ko'
            builtin_path = os.path.join('/lib/modules/', uname_kernel_release.strip(),
                                        'modules.builtin')
            with open(builtin_path) as builtins:
                for line in builtins:
                    if line.endswith(module_file):
                        present = True
                        break
    except IOError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc(), **result)

    # Add/remove module as needed
    if state == 'present':
        if not present:
            if not module.check_mode:
                command = [module.get_bin_path('modprobe', True), name]
                command.extend(shlex.split(params))
                rc, out, err = module.run_command(command)
                if rc != 0:
                    module.fail_json(msg=err, rc=rc, stdout=out, stderr=err, **result)
            result['changed'] = True
    elif state == 'absent':
        if present:
            if not module.check_mode:
                rc, out, err = module.run_command([module.get_bin_path('modprobe', True), '-r', name])
                if rc != 0:
                    module.fail_json(msg=err, rc=rc, stdout=out, stderr=err, **result)
            result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()

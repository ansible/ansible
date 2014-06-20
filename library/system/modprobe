#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013, David Stygstra <david.stygstra@gmail.com>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
module: modprobe
short_description: Add or remove kernel modules
requirements: []
version_added: 1.4
author: David Stygstra, Julien Dauphant, Matt Jeffery
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
- modprobe: name=8021q state=present
# Add the dummy module
- modprobe: name=dummy state=present params="numdummies=2"
'''

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
    except IOError, e:
        module.fail_json(msg=str(e), **args)

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
            rc, _, err = module.run_command(['modprobe', args['name'], args['params']])
            if rc != 0:
                module.fail_json(msg=err, **args)
            args['changed'] = True
    elif args['state'] == 'absent':
        if present:
            rc, _, err = module.run_command(['rmmod', args['name']])
            if rc != 0:
                module.fail_json(msg=err, **args)
            args['changed'] = True

    module.exit_json(**args)

# import module snippets
from ansible.module_utils.basic import *
main()

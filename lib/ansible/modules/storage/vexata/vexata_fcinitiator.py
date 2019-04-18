#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Sandeep Kasargod (sandeep@vexata.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: vexata_fcinitiator
version_added: 2.9
short_description: Manage Fibre Channel initiators on Vexata VX100 storage arrays
description:
    - Adds or removes Fibre Channel (FC) initiators on a Vexata VX100 array.
author:
  - Sandeep Kasargod (@vexata)
options:
  name:
    description:
    - Initiator name.
    required: true
    type: str
  state:
    description:
    - Add initiator when present or remove when absent.
    - Initiators that are in one or more initiator groups cannot be deleted
      without first deleting those initiator groups.
    default: present
    choices: [ present, absent ]
    type: str
  wwn:
    description:
    - FC wwn of Host HBA port for adding a new initiator.
    type: str
extends_documentation_fragment:
    - vexata.vx100
'''

EXAMPLES = r'''
- name: Add initiator named host1fc1 for host HBA port
  vexata_initiator:
    name: host1fc1
    wwn: "01:23:45:67:89:ab:cd:ef"
    state: present
    array: vx100_ultra.test.com
    user: admin
    password: secret

- name: Remove initiator named host1fc1
  vexata_initiator:
    name: host1fc1
    state: absent
    array: vx100_ultra.test.com
    user: admin
    password: secret
'''

RETURN = r'''
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vexata import (
    argument_spec, get_array, required_together)

WWN_RE = re.compile(r'(?:[0-9a-f]{2}:){7}[0-9a-f]{2}')


def validate_wwn(module, err_msg):
    wwn = module.params.get('wwn', False)
    if not wwn:
        module.fail_json(msg=err_msg)
    wwn = wwn.strip().lower()
    if not WWN_RE.match(wwn):
        module.fail_json(msg='wwn should have 01:23:45:67:89:ab:cd:ef format')
    return wwn


def get_initiator(module, array):
    """Retrieve a named initiator if it exists, None if absent."""
    name = module.params['name']
    try:
        inis = array.list_initiators()
        ini = filter(lambda i: i['name'] == name, inis)
        if len(ini) == 1:
            return ini[0]
        else:
            return None
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve initiators.')


def add_initiator(module, array):
    """"Add a host FC initiator."""
    changed = False
    wwn = validate_wwn(module, 'wwn is required for adding initiator.')
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        ini = array.add_initiator(
            module.params['name'],
            'Ansible FC initiator',
            wwn)
        if ini:
            module.log(msg='Added initiator {0}'.format(ini['id']))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Initiator {0} add failed.'.format(wwn))
    module.exit_json(changed=changed)


def remove_initiator(module, array, ini):
    changed = False
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        ini_id = ini['id']
        ok = array.remove_initiator(
            ini_id)
        if ok:
            module.log(msg='Initiator {0} removed.'.format(ini_id))
            changed = True
        else:
            module.fail_json(msg='Initiator {0} remove failed.'.format(ini_id))
    except Exception:
        pass
    module.exit_json(changed=changed)


def main():
    arg_spec = argument_spec()
    arg_spec.update(
        dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            wwn=dict(type='str')
        )
    )

    module = AnsibleModule(arg_spec,
                           supports_check_mode=True,
                           required_together=required_together())

    state = module.params['state']
    array = get_array(module)
    ini = get_initiator(module, array)

    if state == 'present' and not ini:
        add_initiator(module, array)
    elif state == 'absent' and ini:
        remove_initiator(module, array, ini)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()

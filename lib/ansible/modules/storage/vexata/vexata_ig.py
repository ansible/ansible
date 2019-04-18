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
module: vexata_ig
version_added: 2.9
short_description: Manage initiator groups on Vexata VX100 storage arrays
description:
    - Create, deletes or modify initiator groups on a Vexata VX100 array.
author:
  - Sandeep Kasargod (@vexata)
options:
  name:
    description:
      - Initiator group name.
    required: true
    type: str
  state:
    description:
    - Creates/Modifies initiator group when present or delete when absent.
    - Initiator groups that are in one or more export groups cannot be deleted
      without first deleting those export groups.
    default: present
    choices: [ present, absent ]
    type: str
  initiators:
    description:
    - List of initiator names.
    type: list
  hostprofile:
    description:
    - Profile for host OS related differences.
    default: none
    choices: [ none, hpux, aix ]
    type: str
extends_documentation_fragment:
    - vexata.vx100
'''

EXAMPLES = r'''
- name: Create initiator group named dbhosts with two initiators.
  vexata_ig:
    name: dbhosts
    initiators:
    - host1fc1
    - host2fc1
    state: present
    array: vx100_ultra.test.com
    user: admin
    password: secret

- name: Modify existing initiator group named dbhosts to have 3 initiators.
  vexata_ig:
    name: dbhosts
    initiators:
    - host1fc1
    - host2fc1
    - host3fc1
    state: present
    array: vx100_ultra.test.com
    user: admin
    password: secret

- name: Remove initiator group named dbhosts
  vexata_ig:
    name: dbhosts
    state: absent
    array: vx100_ultra.test.com
    user: admin
    password: secret
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vexata import (
    argument_spec, get_array, required_together)


def get_ig(module, array):
    """Retrieve a named ig if it exists, None if absent."""
    name = module.params['name']
    try:
        igs = array.list_igs()
        ig = filter(lambda ig: ig['name'] == name, igs)
        if len(ig) == 1:
            return ig[0]
        else:
            return None
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve initiator groups.')


def get_ini_ids(module, array):
    """Retrieve ids of named initiators."""
    initiators = module.params['initiators']
    if not initiators:
        module.fail_json(msg='Need at least one initiator when creating '
                         'an initiator group.')

    ini_names = frozenset(initiators)
    try:
        all_inis = array.list_initiators()
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve initiators.')

    found_inis = filter(lambda ini: ini['name'] in ini_names, all_inis)
    found_names = frozenset(ini['name'] for ini in found_inis)
    missing_names = list(ini_names.difference(found_names))
    if len(missing_names) > 0:
        module.fail_json(msg='The following initiator names were not found: '
                             '{0}'.format(missing_names))
    # all present
    return [ini['id'] for ini in found_inis]


def create_ig(module, array):
    """"Create a new initiator group."""
    changed = False
    ig_name = module.params['name']
    profile = module.params['hostprofile']
    ini_ids = get_ini_ids(module, array)
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        ig = array.create_ig(
            ig_name,
            'Ansible initiator group',
            ini_ids,
            profile.upper())
        if ig:
            module.log(msg='Created initiator group {0}'.format(ig_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Initiator group {0} create failed.'.format(ig_name))
    module.exit_json(changed=changed)


def update_ig(module, array, ig):
    changed = False
    ig_name = ig['name']
    profile = module.params['hostprofile']
    if profile.upper() != ig['hostProfileType']:
        module.fail_json(msg='Modifying the hostprofile is not supported. '
                             'Delete the initiator group and create a new one.')

    curr_ini_ids = frozenset(ig['currInitiators'])
    new_ini_ids = frozenset(get_ini_ids(module, array))
    add_ini_ids = new_ini_ids.difference(curr_ini_ids)
    rm_ini_ids = curr_ini_ids.difference(new_ini_ids)
    if len(rm_ini_ids) == len(add_ini_ids) == 0:
        msg = 'No update to initiator group {0} required'.format(ig_name)
        module.log(msg=msg)
        module.exit_json(msg=msg, changed=False)

    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        updtig = array.modify_ig(
            ig['id'],
            ig_name,
            ig['description'],
            list(add_ini_ids),
            list(rm_ini_ids))
        if updtig:
            module.log(msg='Modified initiator group {0}'.format(ig_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Initiator group {0} modify failed.'.format(ig_name))
    module.exit_json(changed=changed)


def delete_ig(module, array, ig):
    changed = False
    ig_name = ig['name']
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        ok = array.delete_ig(
            ig['id'])
        if ok:
            module.log(msg='Initiator group {0} deleted.'.format(ig_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Initiator group {0} delete failed.'.format(ig_name))
    module.exit_json(changed=changed)


def main():
    arg_spec = argument_spec()
    arg_spec.update(
        dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            initiators=dict(type='list'),
            hostprofile=dict(type='str', default='none', choices=['none', 'hpux', 'aix'])
        )
    )

    module = AnsibleModule(arg_spec,
                           supports_check_mode=True,
                           required_together=required_together())

    state = module.params['state']
    array = get_array(module)
    ig = get_ig(module, array)

    if state == 'present':
        if not ig:
            create_ig(module, array)
        else:
            update_ig(module, array, ig)
    elif state == 'absent' and ig:
        delete_ig(module, array, ig)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()

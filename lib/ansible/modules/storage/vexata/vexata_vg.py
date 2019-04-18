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
module: vexata_vg
version_added: 2.9
short_description: Manage volume groups on Vexata VX100 storage arrays
description:
    - Create, deletes or modify volume groups on a Vexata VX100 array.
author:
  - Sandeep Kasargod (@vexata)
options:
  name:
    description:
      - Volume group name.
    required: true
    type: str
  state:
    description:
    - Creates/Modifies volume group when present or delete when absent.
    - Volume groups that are in one or more export groups cannot be deleted
      without first deleting those export groups.
    default: present
    choices: [ present, absent ]
    type: str
  volumes:
    description:
    - List of volume/snapshot names.
    type: list
extends_documentation_fragment:
    - vexata.vx100
'''

EXAMPLES = r'''
- name: Create volume group named dbvols with two volumes.
  vexata_vg:
    name: dbvols
    volumes:
    - main
    - replaylog
    state: present
    array: vx100_ultra.test.com
    user: admin
    password: secret

- name: Modify existing volume group named dbvols to have 3 volumes.
  vexata_vg:
    name: dbvols
    volumes:
    - main
    - replaylog
    - scratch
    state: present
    array: vx100_ultra.test.com
    user: admin
    password: secret

- name: Remove volume group named dbvols
  vexata_vg:
    name: dbvols
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


def get_vg(module, array):
    """Retrieve a named vg if it exists, None if absent."""
    name = module.params['name']
    try:
        vgs = array.list_vgs()
        vg = filter(lambda vg: vg['name'] == name, vgs)
        if len(vg) == 1:
            return vg[0]
        else:
            return None
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve volume groups.')


def get_vol_ids(module, array):
    """Retrieve ids of named volumes."""
    volumes = module.params['volumes']
    if not volumes:
        module.fail_json(msg='Need at least one volume when creating '
                         'a volume group.')

    vol_names = frozenset(volumes)
    try:
        all_vols = array.list_volumes()
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve volumes.')

    found_vols = filter(lambda vol: vol['name'] in vol_names, all_vols)
    found_names = frozenset(vol['name'] for vol in found_vols)
    missing_names = list(vol_names.difference(found_names))
    if len(missing_names) > 0:
        module.fail_json(msg='The following volume names were not found: '
                             '{0}'.format(missing_names))
    # all present
    return [vol['id'] for vol in found_vols]


def create_vg(module, array):
    """"Create a new volume group."""
    changed = False
    vg_name = module.params['name']
    vol_ids = get_vol_ids(module, array)
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        vg = array.create_vg(
            vg_name,
            'Ansible volume group',
            vol_ids)
        if vg:
            module.log(msg='Created volume group {0}'.format(vg_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Volume group {0} create failed.'.format(vg_name))
    module.exit_json(changed=changed)


def update_vg(module, array, vg):
    changed = False
    vg_name = vg['name']
    curr_vol_ids = frozenset(vg['currVolumes'])
    new_vol_ids = frozenset(get_vol_ids(module, array))
    add_vol_ids = new_vol_ids.difference(curr_vol_ids)
    rm_vol_ids = curr_vol_ids.difference(new_vol_ids)
    if len(rm_vol_ids) == len(add_vol_ids) == 0:
        msg = 'No update to volume group {0} required'.format(vg_name)
        module.log(msg=msg)
        module.exit_json(msg=msg, changed=False)

    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        updtvg = array.modify_vg(
            vg['id'],
            vg_name,
            vg['description'],
            list(add_vol_ids),
            list(rm_vol_ids))
        if updtvg:
            module.log(msg='Modified volume group {0}'.format(vg_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Volume group {0} modify failed.'.format(vg_name))
    module.exit_json(changed=changed)


def delete_vg(module, array, vg):
    changed = False
    vg_name = vg['name']
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        ok = array.delete_vg(
            vg['id'])
        if ok:
            module.log(msg='Volume group {0} deleted.'.format(vg_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Volume group {0} delete failed.'.format(vg_name))
    module.exit_json(changed=changed)


def main():
    arg_spec = argument_spec()
    arg_spec.update(
        dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            volumes=dict(type='list')
        )
    )

    module = AnsibleModule(arg_spec,
                           supports_check_mode=True,
                           required_together=required_together())

    state = module.params['state']
    array = get_array(module)
    vg = get_vg(module, array)

    if state == 'present':
        if not vg:
            create_vg(module, array)
        else:
            update_vg(module, array, vg)
    elif state == 'absent' and vg:
        delete_vg(module, array, vg)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()

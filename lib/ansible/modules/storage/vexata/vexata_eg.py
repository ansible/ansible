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
module: vexata_eg
version_added: 2.9
short_description: Manage export groups on Vexata VX100 storage arrays
description:
    - Create or delete export groups on a Vexata VX100 array.
    - An export group is a tuple of a volume group, initiator group and port
      group that allows a set of volumes to be exposed to one or more hosts
      through specific array ports.
author:
  - Sandeep Kasargod (@vexata)
options:
  name:
    description:
      - Export group name.
    required: true
    type: str
  state:
    description:
    - Creates export group when present or delete when absent.
    default: present
    choices: [ present, absent ]
    type: str
  vg:
    description:
    - Volume group name.
    type: str
  ig:
    description:
    - Initiator group name.
    type: str
  pg:
    description:
    - Port group name.
    type: str
extends_documentation_fragment:
    - vexata.vx100
'''

EXAMPLES = r'''
- name: Create export group named db_export.
  vexata_eg:
    name: db_export
    vg: dbvols
    ig: dbhosts
    pg: pg1
    state: present
    array: vx100_ultra.test.com
    user: admin
    password: secret

- name: Delete export group named db_export
  vexata_eg:
    name: db_export
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


def get_eg(module, array):
    """Retrieve a named vg if it exists, None if absent."""
    name = module.params['name']
    try:
        egs = array.list_egs()
        eg = filter(lambda eg: eg['name'] == name, egs)
        if len(eg) == 1:
            return eg[0]
        else:
            return None
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve export groups.')


def get_vg_id(module, array):
    """Retrieve a named vg's id if it exists, error if absent."""
    name = module.params['vg']
    try:
        vgs = array.list_vgs()
        vg = filter(lambda vg: vg['name'] == name, vgs)
        if len(vg) == 1:
            return vg[0]['id']
        else:
            module.fail_json(msg='Volume group {0} was not found.'.format(name))
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve volume groups.')


def get_ig_id(module, array):
    """Retrieve a named ig's id if it exists, error if absent."""
    name = module.params['ig']
    try:
        igs = array.list_igs()
        ig = filter(lambda ig: ig['name'] == name, igs)
        if len(ig) == 1:
            return ig[0]['id']
        else:
            module.fail_json(msg='Initiator group {0} was not found.'.format(name))
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve initiator groups.')


def get_pg_id(module, array):
    """Retrieve a named pg's id if it exists, error if absent."""
    name = module.params['pg']
    try:
        pgs = array.list_pgs()
        pg = filter(lambda pg: pg['name'] == name, pgs)
        if len(pg) == 1:
            return pg[0]['id']
        else:
            module.fail_json(msg='Port group {0} was not found.'.format(name))
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve port groups.')


def create_eg(module, array):
    """"Create a new export group."""
    changed = False
    eg_name = module.params['name']
    vg_id = get_vg_id(module, array)
    ig_id = get_ig_id(module, array)
    pg_id = get_pg_id(module, array)
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        eg = array.create_eg(
            eg_name,
            'Ansible export group',
            (vg_id, ig_id, pg_id))
        if eg:
            module.log(msg='Created export group {0}'.format(eg_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Export group {0} create failed.'.format(eg_name))
    module.exit_json(changed=changed)


def delete_eg(module, array, eg):
    changed = False
    eg_name = eg['name']
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        ok = array.delete_eg(
            eg['id'])
        if ok:
            module.log(msg='Export group {0} deleted.'.format(eg_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Export group {0} delete failed.'.format(eg_name))
    module.exit_json(changed=changed)


def main():
    arg_spec = argument_spec()
    arg_spec.update(
        dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            vg=dict(type='str'),
            ig=dict(type='str'),
            pg=dict(type='str')
        )
    )

    module = AnsibleModule(arg_spec,
                           supports_check_mode=True,
                           required_together=required_together())

    state = module.params['state']
    array = get_array(module)
    eg = get_eg(module, array)

    if state == 'present' and not eg:
        create_eg(module, array)
    elif state == 'absent' and eg:
        delete_eg(module, array, eg)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()

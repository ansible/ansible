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
module: vexata_pg
version_added: 2.9
short_description: Manage port groups on Vexata VX100 storage arrays
description:
    - Create, deletes or modify port groups on a Vexata VX100 array.
author:
  - Sandeep Kasargod (@vexata)
options:
  name:
    description:
      - Port group name.
    required: true
    type: str
  state:
    description:
    - Creates/Modifies port group when present or delete when absent.
    - Port groups that are in one or more export groups cannot be deleted
      without first deleting those export groups.
    default: present
    choices: [ present, absent ]
    type: str
  ports:
    description:
    - List of array port ids, the port id range is 0-15.
    type: list
extends_documentation_fragment:
    - vexata.vx100
'''

EXAMPLES = r'''
- name: Create port group named pg1 with four ports.
  vexata_pg:
    name: pg1
    ports:
    - 0
    - 1
    - 8
    - 9
    state: present
    array: vx100_ultra.test.com
    user: admin
    password: secret

- name: Modify existing port group named pg1 to have 6 ports.
  vexata_pg:
    name: pg1
    ports:
    - 0
    - 1
    - 2
    - 8
    - 9
    - 10
    state: present
    array: vx100_ultra.test.com
    user: admin
    password: secret

- name: Remove port group named pg1
  vexata_pg:
    name: pg1
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


def get_pg(module, array):
    """Retrieve a named pg if it exists, None if absent."""
    name = module.params['name']
    try:
        pgs = array.list_pgs()
        pg = filter(lambda pg: pg['name'] == name, pgs)
        if len(pg) == 1:
            return pg[0]
        else:
            return None
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve port groups.')


def get_port_ids(module, array):
    """Check if specified port ids are within bounds for the array."""
    ports = module.params['ports']
    if not ports:
        module.fail_json(msg='Need at least one port id when creating '
                         'a port group.')
    try:
        ports = map(int, ports)
    except ValueError:
        module.fail_json(msg='Port ids must be integers.')

    port_ids = frozenset(ports)
    try:
        all_ports = array.list_saports()
    except Exception:
        module.fail_json(msg='Error while attempting to retrieve port ids.')

    found_ports = filter(lambda port: port['id'] in port_ids, all_ports)
    found_port_ids = frozenset(port['id'] for port in found_ports)
    missing_port_ids = list(port_ids.difference(found_port_ids))
    if len(missing_port_ids) > 0:
        module.fail_json(msg='The following port ids were not found:'
                             '{0}'.format(missing_port_ids))
    # all present
    return list(found_port_ids)


def create_pg(module, array):
    """"Create a new port group."""
    changed = False
    pg_name = module.params['name']
    port_ids = get_port_ids(module, array)
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        pg = array.create_pg(
            pg_name,
            'Ansible port group',
            port_ids)
        if pg:
            module.log(msg='Created port group {0}'.format(pg_name))
            changed = True
        else:
            module.fail_json(msg='Port group {0} create failed.'.format(pg_name))
    except Exception as e:
        pass
    module.exit_json(changed=changed)


def update_pg(module, array, pg):
    changed = False
    pg_name = pg['name']
    curr_port_ids = frozenset(pg['currPorts'])
    new_port_ids = frozenset(get_port_ids(module, array))
    add_port_ids = new_port_ids.difference(curr_port_ids)
    rm_port_ids = curr_port_ids.difference(new_port_ids)
    if len(rm_port_ids) == len(add_port_ids) == 0:
        module.log(msg='No update to port group {0} required'.format(pg_name))
        module.exit_json(changed=False)

    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        updtpg = array.modify_pg(
            pg['id'],
            pg_name,
            pg['description'],
            list(add_port_ids),
            list(rm_port_ids))
        if updtpg:
            module.log(msg='Modified port group {0}'.format(pg_name))
            changed = True
        else:
            module.fail_json(msg='Port group create failed.')
    except Exception:
        pass
    module.exit_json(changed=changed)


def delete_pg(module, array, pg):
    changed = False
    pg_name = pg['name']
    if module.check_mode:
        module.exit_json(changed=changed)

    try:
        ok = array.delete_pg(
            pg['id'])
        if ok:
            module.log(msg='Port group {0} deleted.'.format(pg_name))
            changed = True
        else:
            raise Exception
    except Exception:
        module.fail_json(msg='Port group {0} delete failed.'.format(pg_name))
    module.exit_json(changed=changed)


def main():
    arg_spec = argument_spec()
    arg_spec.update(
        dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            ports=dict(type='list')
        )
    )

    module = AnsibleModule(arg_spec,
                           supports_check_mode=True,
                           required_together=required_together())

    state = module.params['state']
    array = get_array(module)
    pg = get_pg(module, array)

    if state == 'present':
        if not pg:
            create_pg(module, array)
        else:
            update_pg(module, array, pg)
    elif state == 'absent' and pg:
        delete_pg(module, array, pg)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()

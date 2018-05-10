#!/usr/bin/python
#
# Copyright (C) 2018 IBM CORPORATION
# Author(s): Tzur Eliyahu <tzure@il.ibm.com>
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ibm_sa_pool
short_description: Handles pools on an IBM Spectrum Accelerate storage array.
version_added: "2.5"

description:
    - "This module creates or deletes pools to be used on
        IBM Spectrum Accelerate storage systems."

options:
    pool:
        description:
            - Pool name
        required: true
    state:
        description:
            - Pool state - Present in order to create a pool,
                Absent in order to delete.
        required: true
        default: "present"
        choices: [ "present", "absent" ]
    size:
        description:
            - Pool size in GB
        required: false
    snapshot_size:
        description:
            - Pool snapshot size in GB
        required: false
    domain:
        description:
            - Adds the pool to the specified domain.
        required: false
    perf_class:
        description:
            - Assigns a perf_class to the pool.
        required: false

extends_documentation_fragment:
    - ibm_storage

author:
    - Tzur Eliyahu (tzure@il.ibm.com)
'''

EXAMPLES = '''
- name: Create new pool.
  ibm_sa_pool:
    name: test_pool
    size: 300
    state: present
    username: admin
    password: secret
    endpoints: hostdev-system

- name: Delete pool.
  ibm_sa_pool:
    name: test_pool
    state: absent
    username: admin
    password: secret
    endpoints: hostdev-system
'''
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ibm_sa_utils import execute_pyxcli_command, \
    connect_ssl, spectrum_accelerate_spec, is_pyxcli_installed


def main():
    argument_spec = spectrum_accelerate_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            pool=dict(required=True),
            size=dict(),
            snapshot_size=dict(),
            domain=dict(),
            perf_class=dict()
        )
    )

    module = AnsibleModule(argument_spec)

    is_pyxcli_installed(module)

    xcli_client = connect_ssl(module)
    pool = xcli_client.cmd.pool_list(
        pool=module.params['pool']).as_single_element
    state = module.params['state']

    state_changed = False
    if state == 'present' and not pool:
        state_changed = execute_pyxcli_command(
            module, 'pool_create', xcli_client)
    if state == 'absent' and pool:
        state_changed = execute_pyxcli_command(
            module, 'pool_delete', xcli_client)

    module.exit_json(changed=state_changed)


if __name__ == '__main__':
    main()

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
module: ibm_sa_vol_map
short_description: Handles volume mapping on an
    IBM Spectrum Accelerate storage array.
version_added: "2.6"

description:
    - "This module maps volumes to or unmaps them from the hosts on
        IBM Spectrum Accelerate storage systems."

options:
    vol:
        description:
            - Volume name.
        required: true
    state:
        description:
            - When the state is present the volume is mapped.
                When the state is absent, the volume is meant to be unmapped.
        required: true
        default: "present"
        choices: [ "present", "absent" ]
    cluster:
        description:
            - Maps the volume to a cluster.
        required: false
    host:
        description:
            - Maps the volume to a host.
        required: false
    lun:
        description:
            - The LUN identifier.
        required: false
    override:
        description:
            - Overrides the existing volume mapping.
        required: false

extends_documentation_fragment:
    - ibm_storage

author:
    - Tzur Eliyahu (tzure@il.ibm.com)
'''

EXAMPLES = '''
- name: Map volume to host.
  ibm_sa_vol_map:
    vol: ansible_test_vol
    lun: 1
    host: test_host
    username: admin
    password: secret
    endpoints: hostdev-system
    state: present

- name: Map volume to cluster.
  ibm_sa_vol_map:
    vol: ansible_test_vol
    lun: 1
    cluster: test_cluster
    username: admin
    password: secret
    endpoints: hostdev-system
    state: present

- name: Unmap volume.
  ibm_sa_vol_map:
    host: test_host
    username: admin
    password: secret
    endpoints: hostdev-system
    state: absent
'''
RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ibm_sa_utils import execute_pyxcli_command, \
    connect_ssl, spectrum_accelerate_spec, is_pyxcli_installed


def main():
    argument_spec = spectrum_accelerate_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            vol=dict(required=True),
            lun=dict(),
            cluster=dict(),
            host=dict(),
            override=dict()
        )
    )

    module = AnsibleModule(argument_spec)
    is_pyxcli_installed(module)

    xcli_client = connect_ssl(module)
    # required args
    mapping = False
    try:
        mapped_hosts = xcli_client.cmd.vol_mapping_list(
            vol=module.params.get('vol')).as_list
        for host in mapped_hosts:
            if host['host'] == module.params.get("host", ""):
                mapping = True
    except Exception:
        pass
    state = module.params['state']

    state_changed = False
    if state == 'present' and not mapping:
        state_changed = execute_pyxcli_command(module, 'map_vol', xcli_client)
    if state == 'absent' and mapping:
        state_changed = execute_pyxcli_command(
            module, 'unmap_vol', xcli_client)

    module.exit_json(changed=state_changed)


if __name__ == '__main__':
    main()

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
module: ibm_sa_host_ports
short_description: Add host ports on an IBM Spectrum Accelerate storage array.
version_added: "2.6"

description:
    - "This module adds ports to or removes them from the hosts
        on IBM Spectrum Accelerate storage systems."

options:
    host:
        description:
            - The host name.
        required: true
    state:
        description:
            - When the state is present, the port is to be added.
                When the state is abesnt, the port is to be removed.
        required: true
        default: "present"
        choices: [ "present", "absent" ]
    iscsi_name:
        description:
            - iSCSI initiator name.
        required: false
    fcaddress:
        description:
            - Fiber channel address.
        required: false
    num_of_visible_targets:
        description:
            - Number of visible targets
        required: false

extends_documentation_fragment:
    - ibm_storage

author:
    - Tzur Eliyahu (tzure@il.ibm.com)
'''

EXAMPLES = '''
- name: Add ports for host.
  ibm_sa_host_ports:
    host: test_host
    iscsi_name: iqn.1994-05.com.redhat:c157ebdc6707
    username: admin
    password: secret
    endpoints: hostdev-system
    state: present

- name: Remove ports for host.
  ibm_sa_host_ports:
    host: test_host
    iscsi_name: iqn.1994-05.com.redhat:c157ebdc6707
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
            host=dict(required=True),
            iscsi_name=dict(),
            fcaddress=dict(),
            num_of_visible_targets=dict()
        )
    )

    module = AnsibleModule(argument_spec)
    is_pyxcli_installed(module)

    xcli_client = connect_ssl(module)
    # required args
    ports = None
    try:
        ports = xcli_client.cmd.host_list_ports(
            host=module.params.get('host')).as_list
    except Exception:
        pass
    state = module.params['state']
    port_exists = False
    ports = [port.get('port_name') for port in ports]

    for port in ports:
        if (port in module.params.get('iscsi_name', "") or
                port in module.params.get('fcaddress', "")):
            port_exists = True
    state_changed = False
    if state == 'present' and not port_exists:
        state_changed = execute_pyxcli_command(
            module, 'host_add_port', xcli_client)
    if state == 'absent' and port_exists:
        state_changed = execute_pyxcli_command(
            module, 'host_remove_port', xcli_client)

    module.exit_json(changed=state_changed)


if __name__ == '__main__':
    main()

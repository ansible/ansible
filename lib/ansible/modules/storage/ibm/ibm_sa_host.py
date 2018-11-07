#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2018 IBM CORPORATION
# Author(s): Tzur Eliyahu <tzure@il.ibm.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ibm_sa_host
short_description: Adds hosts to or removes them from IBM Spectrum Accelerate Family storage systems.
version_added: "2.7"

description:
    - "This module adds hosts to or removes them from IBM Spectrum Accelerate Family storage systems."

options:
    host:
        description:
            - Host name.
        required: true
    state:
        description:
            - Host state.
        required: true
        default: "present"
        choices: [ "present", "absent" ]
    cluster:
        description:
            - The name of the cluster to include the host.
        required: false
    domain:
        description:
            - The domains the cluster will be attached to.
                To include more than one domain,
                separate domain names with commas.
                To include all existing domains, use an asterisk ("*").
        required: false
    iscsi_chap_name:
        description:
            - The host's CHAP name identifier
        required: false
    iscsi_chap_secret:
        description:
            - The password of the initiator used to
                authenticate to the system when CHAP is enable
        required: false

extends_documentation_fragment:
    - ibm_storage

author:
    - Tzur Eliyahu (@tzure)
'''

EXAMPLES = '''
- name: Define new host.
  ibm_sa_host:
    host: host_name
    state: present
    username: admin
    password: secret
    endpoints: hostdev-system

- name: Delete host.
  ibm_sa_host:
    host: host_name
    state: absent
    username: admin
    password: secret
    endpoints: hostdev-system
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
            cluster=dict(),
            domain=dict(),
            iscsi_chap_name=dict(),
            iscsi_chap_secret=dict()
        )
    )

    module = AnsibleModule(argument_spec)

    is_pyxcli_installed(module)

    xcli_client = connect_ssl(module)
    host = xcli_client.cmd.host_list(
        host=module.params['host']).as_single_element
    state = module.params['state']

    state_changed = False
    if state == 'present' and not host:
        state_changed = execute_pyxcli_command(
            module, 'host_define', xcli_client)
    elif state == 'absent' and host:
        state_changed = execute_pyxcli_command(
            module, 'host_delete', xcli_client)

    module.exit_json(changed=state_changed)


if __name__ == '__main__':
    main()

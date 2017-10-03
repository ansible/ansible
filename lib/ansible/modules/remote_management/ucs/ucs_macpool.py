#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ucs_macpool
short_description: Configures MAC address pools on Cisco UCS Manager
description:
- Configures MAC address pools and MAC pool blocks on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify MAC pool is present and will create if needed.
    - If C(absent), will verify MAC pool is absent and will delete if needed.
    choices: [present, absent]
    default: present
  mac_list:
    description:
    - List of MAC pools specifying the name of the pool, order of addresses,
      and MAC address block from/to.
    required: yes
  org_dn:
    description:
    - Org dn (distinguished name)
    default: org-root
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.5'
'''

EXAMPLES = r'''
- name: Configure MAC address pool
  ucs_macpool:
    hostname: 172.16.143.150
    username: admin
    password: password
    mac_list:
      - name: mac-A
        from: 00:25:B5:00:66:00
        to: 00:25:B5:00:67:F3
        order: sequential
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ucs import UcsConnection, ucs_argument_spec


def _argument_mo():
    return dict(
        mac_list=dict(required=True, type='list'),
        org_dn=dict(type='str', default='org-root'),
    )


def _argument_custom():
    return dict(
        state=dict(default='present',
                   choices=['present', 'absent'],
                   type='str'),
    )


def _argument_connection():
    return dict(
        # UcsHandle
        login_handle=dict(type='dict'),
    )


def _ansible_module_create():
    argument_spec = ucs_argument_spec
    argument_spec.update(_argument_mo())
    argument_spec.update(_argument_custom())
    argument_spec.update(_argument_connection())

    return AnsibleModule(argument_spec,
                         supports_check_mode=True)


def _get_mo_params(params):
    args = {}
    for key in _argument_mo():
        if params.get(key) is None:
            continue
        args[key] = params.get(key)
    return args


def setup_macpool(login_handle, module):
    from ucsmsdk.mometa.macpool.MacpoolPool import MacpoolPool
    from ucsmsdk.mometa.macpool.MacpoolBlock import MacpoolBlock

    ansible = module.params
    args_mo = _get_mo_params(ansible)

    changed = False

    for mac in args_mo['mac_list']:
        exists = False
        dn = args_mo['org_dn'] + '/mac-pool-' + mac['name']
        mo = login_handle.query_dn(dn)
        if mo:
            # check top-level mo props
            kwargs = {}
            kwargs['assignment_order'] = mac['order']
            if (mo.check_prop_match(**kwargs)):
                # top-level props match, check next level props
                if(mac['to'] != '' and mac['from'] != ''):
                    block_dn = dn + '/block-' + mac['from'] + '-' + mac['to']
                    mo_1 = login_handle.query_dn(block_dn)
                    if mo_1:
                        exists = True
                else:
                    exists = True

        if ansible['state'] == 'absent':
            if exists:
                changed = True
                if not module.check_mode:
                    login_handle.remove_mo(mo)
                    login_handle.commit()
        else:
            if not exists:
                changed = True
                if not module.check_mode:
                    # create if mo does not already exist
                    if 'description' not in mac:
                        mac['description'] = ''
                    mo = MacpoolPool(parent_mo_or_dn=args_mo['org_dn'],
                                     name=mac['name'],
                                     descr=mac['description'],
                                     assignment_order=mac['order'])

                    if(mac['to'] != '' and mac['from'] != ''):
                        mo_1 = MacpoolBlock(parent_mo_or_dn=mo,
                                            to=mac['to'],
                                            r_from=mac['from'])
                    login_handle.add_mo(mo, True)
                    login_handle.commit()

    return changed


def setup(login_handle, module):
    result = {}
    err = False

    try:
        result['changed'] = setup_macpool(login_handle, module)
    except Exception as e:
        err = True
        result['msg'] = "setup error: %s " % str(e)
        result['changed'] = False

    return result, err


def main():
    module = _ansible_module_create()
    conn = UcsConnection(module)
    login_handle = conn.login()
    result, err = setup(login_handle, module)
    conn.logout()
    if err:
        module.fail_json(**result)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

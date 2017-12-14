#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
    - List of MAC pools which contain the following properties
    - name (Name of the MAC pool (required))
    - descr (Description for the MAC pool)
    - order (Assignment order which is default or sequential)
    - first_addr (First MAC address in the MAC addresses block)
    - last_addr (Last MAC address in the MAC addresses block)
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
        first_addr: 00:25:B5:00:66:00
        last_addr: 00:25:B5:00:67:F3
        order: sequential
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(mac_list=dict(required=True, type='list'),
                         org_dn=dict(type='str', default='org-root'),
                         state=dict(default='present', choices=['present', 'absent'], type='str'))
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.macpool.MacpoolPool import MacpoolPool
    from ucsmsdk.mometa.macpool.MacpoolBlock import MacpoolBlock

    changed = False
    try:
        for mac in module.params['mac_list']:
            exists = False
            dn = module.params['org_dn'] + '/mac-pool-' + mac['name']
            mo = ucs.login_handle.query_dn(dn)
            if mo:
                # check top-level mo props
                kwargs = {}
                if 'order' in mac:
                    kwargs['assignment_order'] = mac['order']
                if 'descr' in mac:
                    kwargs['descr'] = mac['descr']
                if (mo.check_prop_match(**kwargs)):
                    # top-level props match, check next level mo/props
                    if 'last_addr' in mac and 'first_addr' in mac:
                        block_dn = dn + '/block-' + mac['first_addr'].upper() + '-' + mac['last_addr'].upper()
                        mo_1 = ucs.login_handle.query_dn(block_dn)
                        if mo_1:
                            exists = True
                    else:
                        exists = True

            if module.params['state'] == 'absent':
                if exists:
                    if not module.check_mode:
                        ucs.login_handle.remove_mo(mo)
                        ucs.login_handle.commit()
                    changed = True
            else:
                if not exists:
                    if not module.check_mode:
                        # create if mo does not already exist
                        if 'order' not in mac:
                            mac['order'] = 'default'
                        if 'descr' not in mac:
                            mac['descr'] = ''
                        mo = MacpoolPool(parent_mo_or_dn=module.params['org_dn'],
                                         name=mac['name'],
                                         descr=mac['descr'],
                                         assignment_order=mac['order'])

                        if 'last_addr' in mac and 'first_addr' in mac:
                            mo_1 = MacpoolBlock(parent_mo_or_dn=mo,
                                                to=mac['last_addr'],
                                                r_from=mac['first_addr'])
                        ucs.login_handle.add_mo(mo, True)
                        ucs.login_handle.commit()
                    changed = True

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed
    if err:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()

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
module: ucs_wwn_pool
short_description: Configures WWNN or WWPN pools on Cisco UCS Manager
description:
- Configures WWNNs or WWPN pools on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify WWNNs/WWPNs are present and will create if needed.
    - If C(absent), will verify WWNNs/WWPNs are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - Name of the WWNN/WWPN
    required: yes
  purpose:
    description:
    - Specify node (WWNN) or port (WWPN)
    - Optional if state absent
    choices: [node, port]
    required: yes
  descrption:
    description:
    - Description for the WWNN/WWPN pool
    aliases: [ descr ]
  order:
    description:
    - Assignment order
    choices: [default, sequential]
    default: default
  first_addr:
    description: First WWNN/WWPN address in the WWN addresses block
  last_addr:
    description: Last WWNN/WWPN address in the WWN addresses block
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
- name: Configure WWNN/WWPN pools
  ucs_wwn_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: WWNN-Pool
    purpose: node
    first_addr: 20:00:00:25:B5:48:00:00
    last_addr: 20:00:00:25:B5:48:00:0F
  ucs_wwn_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: WWPN-Pool-A
    purpose: port
    order: sequential
    first_addr: 20:00:00:25:B5:48:0A:00
    last_addr: 20:00:00:25:B5:48:0A:0F

- name: Remove WWNN/WWPN pools
  ucs_wwn_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: WWNN-Pool
    state: absent
  ucs_wwn_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: WWPN-Pool-A
    state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_dn=dict(type='str', default='org-root'),
        name=dict(type='str'),
        purpose=dict(type='str', choices=['node', 'port']),
        descr=dict(type='str'),
        order=dict(type='str', default='default', choices=['default', 'sequential']),
        first_addr=dict(type='str'),
        last_addr=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        wwn_list=dict(type='list'),
    )

    # Note that use of wwn_list is an experimental feature which allows multiple resource updates with a single UCSM connection.
    # Support for wwn_list may change or be removed once persistent UCS connections are supported.
    # Either wwn_list or name is required (user can specify either a list or single resource).

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['wwn_list', 'name']
        ],
        mutually_exclusive=[
            ['wwn_list', 'name']
        ],
    )
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.fcpool.FcpoolInitiators import FcpoolInitiators
    from ucsmsdk.mometa.fcpool.FcpoolBlock import FcpoolBlock

    changed = False
    try:
        # Only documented use is a single resource, but to also support experimental
        # feature allowing multiple updates all params are converted to a wwn_list below.

        if module.params['wwn_list']:
            # directly use the list (single resource and list are mutually exclusive
            wwn_list = module.params['wwn_list']
        else:
            # single resource specified, create list from the current params
            wwn_list = [module.params]
        for wwn in wwn_list:
            mo_exists = False
            props_match = False
            # set default params.  Done here to set values for lists which can't be done in the argument_spec
            if not wwn.get('descr'):
                wwn['descr'] = ''
            if not wwn.get('order'):
                wwn['order'] = 'default'
            # dn is <org_dn>/wwn-pool-<name> for WWNN or WWPN
            dn = module.params['org_dn'] + '/wwn-pool-' + wwn['name']

            mo = ucs.login_handle.query_dn(dn)
            if mo:
                mo_exists = True

            if module.params['state'] == 'absent':
                if mo_exists:
                    if not module.check_mode:
                        ucs.login_handle.remove_mo(mo)
                        ucs.login_handle.commit()
                    changed = True
            else:
                # append purpose param with suffix used by UCSM
                purpose_param = wwn['purpose'] + '-wwn-assignment'
                if mo_exists:
                    # check top-level mo props
                    kwargs = {}
                    kwargs['assignment_order'] = wwn['order']
                    kwargs['descr'] = wwn['descr']
                    kwargs['purpose'] = purpose_param
                    if (mo.check_prop_match(**kwargs)):
                        # top-level props match, check next level mo/props
                        if 'last_addr' in wwn and 'first_addr' in wwn:
                            block_dn = dn + '/block-' + wwn['first_addr'].upper() + '-' + wwn['last_addr'].upper()
                            mo_1 = ucs.login_handle.query_dn(block_dn)
                            if mo_1:
                                props_match = True
                        else:
                            props_match = True

                if not props_match:
                    if not module.check_mode:
                        # create if mo does not already exist
                        mo = FcpoolInitiators(
                            parent_mo_or_dn=module.params['org_dn'],
                            name=wwn['name'],
                            descr=wwn['descr'],
                            assignment_order=wwn['order'],
                            purpose=purpose_param,
                        )
                        if 'last_addr' in wwn and 'first_addr' in wwn:
                            mo_1 = FcpoolBlock(
                                parent_mo_or_dn=mo,
                                to=wwn['last_addr'],
                                r_from=wwn['first_addr'],
                            )

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

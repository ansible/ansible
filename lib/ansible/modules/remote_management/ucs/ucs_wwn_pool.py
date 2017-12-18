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
    - If specifying a single WWNN/WWPN, name is required
  purpose:
    description:
    - Specify node (WWNN) or port (WWPN)
    - If specifying a single WWNN/WWPN, purpose is required
    choices: [node, port]
  descr:
    description:
    - Description for the WWNN/WWPN pool
  order:
    description:
    - Assignment order
    choices: [default, sequential]
    default: default
  first_addr:
    description: First WWNN/WWPN address in the WWN addresses block
  last_addr:
    description: Last WWNN/WWPN address in the WWN addresses block
  wwn_list:
    description:
    - List of WWNNs/WWPN pools
    - wwn_list allows multiple resource updates with a single UCSM connection
    - Each list item contains the following properties
    - name (Name of the WWNN/WWPN pool (required))
    - purporse (node or port (required))
    - descr (Description for the WWNN/WWPN pool)
    - order (Assignment order which is default or sequential)
    - first_addr (First WWNN/WWPN address in the WWN addresses block)
    - last_addr (Last WWNN/WWPN address in the WWN addresses block)
    - Either wwn_list or name/purpose is required
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
- name: Configure multiple WWNN/WWPN pools
  ucs_wwn_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    wwn_list:
      - name: WWNN-Pool
        purpose: node
        first_addr: 20:00:00:25:B5:48:00:00
        last_addr: 20:00:00:25:B5:48:00:0F
      - name: WWPN-Pool-A
        purpose: port
        order: sequential
        first_addr: 20:00:00:25:B5:48:0A:00
        last_addr: 20:00:00:25:B5:48:0A:0F
      - name: WWPN-Pool-B
        purpose: port
        order: sequential
        first_addr: 20:00:00:25:B5:48:0B:00
        last_addr: 20:00:00:25:B5:48:0B:0F

- name: Configure single WWNN pool
  ucs_wwn_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: WWNN-Pool
    purpose: node
    first_addr: 20:00:00:25:B5:58:00:00
    last_addr: 20:00:00:25:B5:58:00:0F
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(wwn_list=dict(type='list'),
                         org_dn=dict(type='str', default='org-root'),
                         name=dict(type='str'),
                         purpose=dict(type='str', choices=['node', 'port']),
                         descr=dict(type='str'),
                         order=dict(type='str', default='default', choices=['default', 'sequential']),
                         first_addr=dict(type='str'),
                         last_addr=dict(type='str'),
                         state=dict(type='str', default='present', choices=['present', 'absent']))
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           required_one_of=[
                               ['wwn_list', 'name']
                           ],
                           mutually_exclusive=[
                               ['wwn_list', 'name']
                           ],
                           required_together=[
                               ['name', 'purpose']
                           ])
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.fcpool.FcpoolInitiators import FcpoolInitiators
    from ucsmsdk.mometa.fcpool.FcpoolBlock import FcpoolBlock

    changed = False
    try:
        if module.params['wwn_list']:
            # directly use the list (single resource and list are mutually exclusive
            wwn_list = module.params['wwn_list']
        else:
            # single resource specified, create list from the current params
            wwn_list = [module.params]
        for wwn in wwn_list:
            exists = False
            # set default params.  Done here to set values for lists which can't be done in the argument_spec
            if not wwn.get('descr'):
                wwn['descr'] = ''
            if not wwn.get('order'):
                wwn['order'] = 'default'
            # append purpose param with suffix used by UCSM
            purpose_param = wwn['purpose'] + '-wwn-assignment'
            # dn is <org_dn>/wwn-pool-<name> for WWNN or WWPN
            dn = module.params['org_dn'] + '/wwn-pool-' + wwn['name']

            mo = ucs.login_handle.query_dn(dn)
            if mo:
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
                        mo = FcpoolInitiators(parent_mo_or_dn=module.params['org_dn'],
                                              name=wwn['name'],
                                              descr=wwn['descr'],
                                              assignment_order=wwn['order'],
                                              purpose=purpose_param)
                        if 'last_addr' in wwn and 'first_addr' in wwn:
                            mo_1 = FcpoolBlock(parent_mo_or_dn=mo,
                                               to=wwn['last_addr'],
                                               r_from=wwn['first_addr'])

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

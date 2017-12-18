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
module: ucs_vsans
short_description: Configures VSANs on Cisco UCS Manager
description:
- Configures VSANs on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify VSANs are present and will create if needed.
    - If C(absent), will verify VSANs are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - Name of the VSAN
    - If specifying a single VSAN, name is required
  vsan_id:
    description:
    - VSAN ID
    - If specifying a single VSAN, vsan_id is required
  vlan_id:
    description:
    - VLAN ID (for FCoE traffic)
    - If specifying a single VSAN, vlan_id is required
  fc_zoning:
    description:
    - Enable/Disable FC Zoning
    - Do not enable local zoning if FI is connected to an upstream FC/FCoE switch
    choices: [disabled, enabled]
    default: disabled
  fabric:
    description:
    - Which fabric
    choices: [common, A, B]
    default: common
  vsan_list:
    description:
    - List of VSANs
    - vsan_list allows multiple resource updates with a single UCSM connection
    - Each list item contains the following properties
    - name (Name of the VSAN pool (required))
    - vsan_id (VSAN ID (required))
    - vlan_id (VLAN ID (required))
    - fc_zoning (disabled (default) or enabled)
    - fabric (common (default), A, or B)
    - Either vsan_list or name/vsan_id/vlan_id is required
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.5'
'''

EXAMPLES = r'''
- name: Configure multiple VSANs
  ucs_vsans:
    hostname: 172.16.143.150
    username: admin
    password: password
    vsan_list:
      - name: vsan110
        vsan_id: '110'
        vlan_id: '110'
      - name: vsan-A-111
        vsan_id: '111'
        vlan_id: '111'
        fabric: A
      - name: vsan-B-112
        vsan_id: '112'
        vlan_id: '112'
        fabric: B
        fc_zoning: enabled

- name: Configure single VSAN
  ucs_vsans:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vsan120
    vsan_id: '120'
    vlan_id: '120'
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(vsan_list=dict(type='list'),
                         name=dict(type='str'),
                         vsan_id=dict(type='str'),
                         vlan_id=dict(type='str'),
                         fc_zoning=dict(type='str', default='disabled', choices=['disabled', 'enabled']),
                         fabric=dict(type='str', default='common', choices=['common', 'A', 'B']),
                         state=dict(type='str', default='present', choices=['present', 'absent']))
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           required_one_of=[
                               ['vsan_list', 'name']
                           ],
                           mutually_exclusive=[
                               ['vsan_list', 'name']
                           ],
                           required_together=[
                               ['name', 'vsan_id', 'vlan_id']
                           ])
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.fabric.FabricVsan import FabricVsan

    changed = False
    try:
        if module.params['vsan_list']:
            # directly use the list (single resource and list are mutually exclusive
            vsan_list = module.params['vsan_list']
        else:
            # single resource specified, create list from the current params
            vsan_list = [module.params]
        for vsan in vsan_list:
            exists = False
            # set default params.  Done here to set values for lists which can't be done in the argument_spec
            if not vsan.get('fc_zoning'):
                vsan['fc_zoning'] = 'disabled'
            if not vsan.get('fabric'):
                vsan['fabric'] = 'common'
            # dn is fabric/san/net-<name> for common vsans or fabric/san/[A or B]/net-<name> for A or B
            dn_base = 'fabric/san'
            if vsan['fabric'] != 'common':
                dn_base += '/' + vsan['fabric']
            dn = dn_base + '/net-' + vsan['name']

            mo = ucs.login_handle.query_dn(dn)
            if mo:
                # check top-level mo props
                kwargs = {}
                kwargs['id'] = vsan['vsan_id']
                kwargs['fcoe_vlan'] = vsan['vlan_id']
                kwargs['zoning_state'] = vsan['fc_zoning']
                if (mo.check_prop_match(**kwargs)):
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
                        mo = FabricVsan(parent_mo_or_dn=dn_base,
                                        name=vsan['name'],
                                        id=vsan['vsan_id'],
                                        fcoe_vlan=vsan['vlan_id'],
                                        zoning_state=vsan['fc_zoning'])

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

#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

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
    - The name assigned to the VSAN.
    - This name can be between 1 and 32 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the VSAN is created.
    required: yes
  vsan_id:
    description:
    - The unique identifier assigned to the VSAN.
    - The ID can be a string between '1' and '4078', or between '4080' and '4093'. '4079' is a reserved VSAN ID.
    - In addition, if you plan to use FC end-host mode, the range between '3840' to '4079' is also a reserved VSAN ID range.
    - Optional if state is absent.
    required: yes
  vlan_id:
    description:
    - The unique string identifier assigned to the VLAN used for Fibre Channel connections.
    - Note that Cisco UCS Manager uses VLAN '4048'.  See the UCS Manager configuration guide if you want to assign '4048' to a VLAN.
    - Optional if state is absent.
    required: yes
  fc_zoning:
    description:
    - Fibre Channel zoning configuration for the Cisco UCS domain.
    - "Fibre Channel zoning can be set to one of the following values:"
    - "disabled — The upstream switch handles Fibre Channel zoning, or Fibre Channel zoning is not implemented for the Cisco UCS domain."
    - "enabled — Cisco UCS Manager configures and controls Fibre Channel zoning for the Cisco UCS domain."
    - If you enable Fibre Channel zoning, do not configure the upstream switch with any VSANs that are being used for Fibre Channel zoning.
    choices: [disabled, enabled]
    default: disabled
  fabric:
    description:
    - "The fabric configuration of the VSAN.  This can be one of the following:"
    - "common - The VSAN maps to the same VSAN ID in all available fabrics."
    - "A - The VSAN maps to the a VSAN ID that exists only in fabric A."
    - "B - The VSAN maps to the a VSAN ID that exists only in fabric B."
    choices: [common, A, B]
    default: common
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.5'
'''

EXAMPLES = r'''
- name: Configure VSAN
  ucs_vsans:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vsan110
    vsan_id: '110'
    vlan_id: '110'

- name: Remove VSAN
  ucs_vsans:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vsan110
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        name=dict(type='str'),
        vsan_id=dict(type='str'),
        vlan_id=dict(type='str'),
        fc_zoning=dict(type='str', default='disabled', choices=['disabled', 'enabled']),
        fabric=dict(type='str', default='common', choices=['common', 'A', 'B']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        vsan_list=dict(type='list'),
    )

    # Note that use of vsan_list is an experimental feature which allows multiple resource updates with a single UCSM connection.
    # Support for vsan_list may change or be removed once persistent UCS connections are supported.
    # Either vsan_list or name/vsan_id/vlan_id is required (user can specify either a list or single resource).

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['vsan_list', 'name']
        ],
        mutually_exclusive=[
            ['vsan_list', 'name']
        ],
    )
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.fabric.FabricVsan import FabricVsan

    changed = False
    try:
        # Only documented use is a single resource, but to also support experimental
        # feature allowing multiple updates all params are converted to a vsan_list below.

        if module.params['vsan_list']:
            # directly use the list (single resource and list are mutually exclusive
            vsan_list = module.params['vsan_list']
        else:
            # single resource specified, create list from the current params
            vsan_list = [module.params]
        for vsan in vsan_list:
            mo_exists = False
            props_match = False
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
                mo_exists = True

            if module.params['state'] == 'absent':
                # mo must exist but all properties do not have to match
                if mo_exists:
                    if not module.check_mode:
                        ucs.login_handle.remove_mo(mo)
                        ucs.login_handle.commit()
                    changed = True
            else:
                if mo_exists:
                    # check top-level mo props
                    kwargs = dict(id=vsan['vsan_id'])
                    kwargs['fcoe_vlan'] = vsan['vlan_id']
                    kwargs['zoning_state'] = vsan['fc_zoning']
                    if (mo.check_prop_match(**kwargs)):
                        props_match = True

                if not props_match:
                    if not module.check_mode:
                        # create if mo does not already exist
                        mo = FabricVsan(
                            parent_mo_or_dn=dn_base,
                            name=vsan['name'],
                            id=vsan['vsan_id'],
                            fcoe_vlan=vsan['vlan_id'],
                            zoning_state=vsan['fc_zoning'],
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

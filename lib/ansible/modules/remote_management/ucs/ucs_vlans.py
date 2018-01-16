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
module: ucs_vlans
short_description: Configures VLANs on Cisco UCS Manager
description:
- Configures VLANs on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify VLANs are present and will create if needed.
    - If C(absent), will verify VLANs are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name assigned to the VLAN.
    - This name can be between 1 and 32 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the VLAN is created.
    required: yes
  id:
    description:
    - The unique string identifier assigned to the VLAN.
    - Note that Cisco UCS Manager uses VLAN '4048'.  See the UCS Manager configuration guide if you want to assign '4048' to a VLAN.
    - Optional if state is absent.
    required: yes
  fabric:
    description:
    - "The fabric configuration of the VLAN.  This can be one of the following:"
    - "common - The VLAN maps to the same VLAN ID in all available fabrics."
    - "A - The VLAN maps to the a VLAN ID that exists only in fabric A."
    - "B - The VLAN maps to the a VLAN ID that exists only in fabric B."
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
- name: Configure VLAN
  ucs_vlans:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vlan2
    id: '2'
    native: 'yes'

- name: Remove VLAN
  ucs_vlans:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vlan2
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
        name=dict(type='str', required=True),
        id=dict(type='str'),
        native=dict(type='str', default='no', choices=['yes', 'no']),
        fabric=dict(type='str', default='common', choices=['common', 'A', 'B']),
        sharing=dict(type='str', default='none', choices=['none']),
        multicast_policy=dict(type='str', default='', choices=['']),   
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['id']],
        ],
    )
    ucs = UCSModule(module)

    err = False

    # UCSModule creation above verifies ucsmsdk is present and exits on failure, so additional imports are done below.
    from ucsmsdk.mometa.fabric.FabricVlan import FabricVlan

    changed = False
    try:
        mo_exists = False
        props_match = False
        # dn is fabric/lan/net-<name> for common vlans or fabric/lan/[A or B]/net-<name> for A or B
        dn_base = 'fabric/lan'
        if module.params['fabric'] != 'common':
            dn_base += '/' + module.params['fabric']
        dn = dn_base + '/net-' + module.params['name']

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
                kwargs = dict(id=module.params['id'])
                kwargs['default_net'] = module.params['native']
                kwargs['sharing'] = module.params['sharing']
                kwargs['mcast_policy_name'] = module.params['multicast_policy']
                if (mo.check_prop_match(**kwargs)):
                    props_match = True

            if not props_match:
                if not module.check_mode:
                    # create if mo does not already exist
                    mo = FabricVlan(
                        parent_mo_or_dn=dn_base,
                        name=module.params['name'],
                        id=module.params['id'],
                        default_net=module.params['native'],
                        sharing=module.params['sharing'],
                        mcast_policy_name=module.params['multicast_policy'],
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

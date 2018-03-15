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
    - The VLAN name is case sensitive.
    - This name can be between 1 and 32 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the VLAN is created.
    required: yes
  multicast_policy:
    description:
    - The multicast policy associated with this VLAN.
    - This option is only valid if the Sharing Type field is set to None or Primary.
    default: ''
  fabric:
    description:
    - "The fabric configuration of the VLAN.  This can be one of the following:"
    - "common - The VLAN applies to both fabrics and uses the same configuration parameters in both cases."
    - "A — The VLAN only applies to fabric A."
    - "B — The VLAN only applies to fabric B."
    - For upstream disjoint L2 networks, Cisco recommends that you choose common to create VLANs that apply to both fabrics.
    choices: [common, A, B]
    default: common
  id:
    description:
    - The unique string identifier assigned to the VLAN.
    - A VLAN ID can be between '1' and '3967', or between '4048' and '4093'.
    - You cannot create VLANs with IDs from 4030 to 4047. This range of VLAN IDs is reserved.
    - The VLAN IDs you specify must also be supported on the switch that you are using.
    - VLANs in the LAN cloud and FCoE VLANs in the SAN cloud must have different IDs.
    - Optional if state is absent.
    required: yes
  sharing:
    description:
    - The Sharing Type field.
    - "Whether this VLAN is subdivided into private or secondary VLANs. This can be one of the following:"
    - "none - This VLAN does not have any secondary or private VLANs. This is a regular VLAN."
    - "primary - This VLAN can have one or more secondary VLANs, as shown in the Secondary VLANs area. This VLAN is a primary VLAN in the private VLAN domain."
    - "isolated - This is a private VLAN associated with a primary VLAN. This VLAN is an Isolated VLAN."
    - "community - This VLAN can communicate with other ports on the same community VLAN as well as the promiscuous port. This VLAN is a Community VLAN."
    choices: [none, primary, isolated, community]
    default: none
  native:
    description:
    - Designates the VLAN as a native VLAN.
    choices: ['yes', 'no']
    default: 'no'
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
        multicast_policy=dict(type='str', default=''),
        fabric=dict(type='str', default='common', choices=['common', 'A', 'B']),
        id=dict(type='str'),
        sharing=dict(type='str', default='none', choices=['none', 'primary', 'isolated', 'community']),
        native=dict(type='str', default='no', choices=['yes', 'no']),
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

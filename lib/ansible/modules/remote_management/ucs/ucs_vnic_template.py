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
module: ucs_vnic_template
short_description: Configures vNIC templates on Cisco UCS Manager
description:
- Configures vNIC templates on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify vNIC templates are present and will create if needed.
    - If C(absent), will verify vNIC templates are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the virtual NIC template.
    - This name can be between 1 and 16 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the template is created.
    required: yes
  description:
    description:
    - A user-defined description of the template.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
  fabric:
    description:
    - The Fabric ID field.
    - The name of the fabric interconnect that vNICs created with this template are associated with.
    choices: [A, B]
    default: A
  redundancy_type:
    description:
    - The Redundancy Type used for template pairing from the Primary or Secondary redundancy template.
    - "primary — Creates configurations that can be shared with the Secondary template."
    - Any other shared changes on the Primary template are automatically synchronized to the Secondary template.
    - "secondary — All shared configurations are inherited from the Primary template."
    - "none - Legacy vNIC template behavior. Select this option if you do not want to use redundancy."
    choices: [none, primary, secondary]
    default: none
  vlan:
    description:
    - The VLAN to associate with vNICs created from this template.
    default: default
  template_type:
    description:
    - The Template Type field.
    - "This can be one of the following:"
    - "initial-template — vNICs created from this template are not updated if the template changes."
    - "updating-template - vNICs created from this template are updated if the template changes."
    choices: [initial-template, updating-template]
    default: initial-template
  max_data:
    description:
    - The Max Data Field Size field.
    - The maximum size of the Fibre Channel frame payload bytes that the vNIC supports.
    - Enter an string between '256' and '2112'.
    default: '2048'
  wwpn_pool:  
    description:
    - The WWPN pool that a vNIC created from this template uses to derive its WWPN address.
    default: default
  qos_policy:
    description:
    - The QoS policy that is associated with vNICs created from this template.
  pin_group:
    description:
    - The LAN pin group that is associated with vNICs created from this template.
  stats_policy:
    description:
    - The statistics collection policy that is associated with vNICs created from this template.
    default: default
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
- name: Configure vNIC template
  ucs_vnic_template:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vNIC-A
    fabric: A
    vlan: VLAN-A
    mac_pool: WWPN-Pool-A

- name: Remove vNIC template
  ucs_vnic_template:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vNIC-A
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
        name=dict(type='str', required=True),
        descr=dict(type='str', default=''),
        fabric=dict(type='str', default='A', choices=['A', 'B']),
        redundancy_type=dict(type='str', default='none', choices=['none', 'primary', 'secondary']),
        vlan=dict(type='str', default='default'),
        template_type=dict(type='str', default='initial-template', choices=['initial-template', 'updating-template']),
        mtu=dict(type='str', default='1500'),
        mac_pool=dict(type='str', default='default'),
        qos_policy=dict(type='str', default=''),
        stats_policy=dict(type='str', default='default'),
        network_ctrl_policy=dict(type='str', default=''),   
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )
    ucs = UCSModule(module)

    err = False

    # UCSModule creation above verifies ucsmsdk is present and exits on failure.  Additional imports are done below.
    from ucsmsdk.mometa.vnic.VnicLanConnTempl import VnicLanConnTempl
    from ucsmsdk.mometa.vnic.VnicEtherIf import VnicEtherIf

    changed = False
    try:
        mo_exists = False
        props_match = False
        # dn is <org_dn>/lan-conn-templ-<name>
        dn = module.params['org_dn'] + '/lan-conn-templ-' + module.params['name']

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
                kwargs = dict(descr=module.params['descr'])
                kwargs['switch_id'] = module.params['fabric']
                kwargs['redundancy_pair_type'] = module.params['redundancy_type']   
                kwargs['templ_type'] = module.params['template_type']
                kwargs['max_data_field_size'] = module.params['max_data']
                kwargs['ident_pool_name'] = module.params['wwpn_pool']
                kwargs['qos_policy_name'] = module.params['qos_policy']
                kwargs['pin_to_group_name'] = module.params['pin_group']
                kwargs['stats_policy_name'] = module.params['stats_policy']
                if (mo.check_prop_match(**kwargs)):
                    # top-level props match, check next level mo/props
                    child_dn = dn + '/if-default'
                    mo_1 = ucs.login_handle.query_dn(child_dn)
                    if mo_1:
                        kwargs = dict(name=module.params['vlan'])
                        if (mo_1.check_prop_match(**kwargs)):
                            props_match = True

            if not props_match:
                if not module.check_mode:
                    # create if mo does not already exist
                    mo = VnicLanConnTempl(
                        parent_mo_or_dn=module.params['org_dn'],
                        name=module.params['name'],
                        descr=module.params['descr'],
                        switch_id=module.params['fabric'],
                        templ_type=module.params['template_type'],
                        ident_pool_name=module.params['mac_pool'],
                        mtu=module.params['mtu'],
                        qos_policy_name=module.params['qos_policy'],
                        stats_policy_name=module.params['stats_policy'],
                        nw_ctrl_policy_name=module.params['network_ctrl_policy'],
                    )

                    mo_1 = VnicEtherIf(
                        parent_mo_or_dn=mo,
                        name=module.params['vlan'],
                        default=module.params['native'],
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

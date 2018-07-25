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
module: ucs_lan_connectivity
short_description: Configures LAN Connectivity Policies on Cisco UCS Manager
description:
- Configures LAN Connectivity Policies on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify LAN Connectivity Policies are present and will create if needed.
    - If C(absent), will verify LAN Connectivity Policies are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the LAN Connectivity Policy.
    - This name can be between 1 and 16 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the policy is created.
    required: yes
  description:
    description:
    - A description of the LAN Connectivity Policy.
    - Cisco recommends including information about where and when to use the policy.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
  vnic_list:
    description:
    - List of vNICs used by the LAN Connectivity Policy.
    - vNICs used by the LAN Connectivity Policy must be created from a vNIC template.
    - "Each list element has the following suboptions:"
    - "= name"
    - "  The name of the vNIC (required)."
    - "= vnic_template"
    - "  The name of the vNIC template (required)."
    - "- adapter_policy"
    - "  The name of the Ethernet adapter policy."
    - "  A user defined policy can be used, or one of the system defined policies."
    - "- order"
    - "  String specifying the vNIC assignment order (e.g., '1', '2')."
    - "  [Default: unspecified]"
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
- name: Configure LAN Connectivity Policy
  ucs_lan_connectivity:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: Cntr-LAN-Boot
    vnic_list:
    - name: Fabric-A
      vnic_template: vNIC-Template-A
      adapter_policy: Linux
    - name: Fabric-B
      vnic_template: vNIC-Template-B
      adapter_policy: Linux

- name: Remove LAN Connectivity Policy
  ucs_lan_connectivity:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: Cntr-LAN-Boot
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
        description=dict(type='str', aliases=['descr'], default=''),
        vnic_list=dict(type='list'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )
    ucs = UCSModule(module)

    err = False

    # UCSModule creation above verifies ucsmsdk is present and exits on failure.  Additional imports are done below.
    from ucsmsdk.mometa.vnic.VnicLanConnPolicy import VnicLanConnPolicy
    from ucsmsdk.mometa.vnic.VnicEther import VnicEther
    from ucsmsdk.mometa.vnic.VnicEtherIf import VnicEtherIf

    changed = False
    try:
        mo_exists = False
        props_match = False
        # dn is <org_dn>/lan-conn-pol-<name>
        dn = module.params['org_dn'] + '/lan-conn-pol-' + module.params['name']

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
            # set default params.  Done here to set values for lists which can't be done in the argument_spec
            if module.params.get('vnic_list'):
                for vnic in module.params['vnic_list']:
                    if not vnic.get('adapter_policy'):
                        vnic['adapter_policy'] = ''
                    if not vnic.get('order'):
                        vnic['order'] = 'unspecified'
            if mo_exists:
                # check top-level mo props
                kwargs = dict(descr=module.params['description'])
                if (mo.check_prop_match(**kwargs)):
                    # top-level props match, check next level mo/props
                    if not module.params.get('vnic_list'):
                        props_match = True
                    else:
                        # check vnicEther props
                        for vnic in module.params['vnic_list']:
                            child_dn = dn + '/ether-' + vnic['name']
                            mo_1 = ucs.login_handle.query_dn(child_dn)
                            if mo_1:
                                kwargs = dict(adaptor_profile_name=vnic['adapter_policy'])
                                kwargs['order'] = vnic['order']
                                kwargs['nw_templ_name'] = vnic['vnic_template']
                                if (mo_1.check_prop_match(**kwargs)):
                                    props_match = True

            if not props_match:
                if not module.check_mode:
                    # create if mo does not already exist
                    mo = VnicLanConnPolicy(
                        parent_mo_or_dn=module.params['org_dn'],
                        name=module.params['name'],
                        descr=module.params['description'],
                    )

                    if module.params.get('vnic_list'):
                        for vnic in module.params['vnic_list']:
                            mo_1 = VnicEther(
                                addr='derived',
                                parent_mo_or_dn=mo,
                                name=vnic['name'],
                                adaptor_profile_name=vnic['adapter_policy'],
                                nw_templ_name=vnic['vnic_template'],
                                order=vnic['order'],
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

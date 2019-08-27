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
    suboptions:
      name:
        description:
        - The name of the vNIC.
        required: yes
      vnic_template:
        description:
        - The name of the vNIC template.
        required: yes
      adapter_policy:
        description:
        - The name of the Ethernet adapter policy.
        - A user defined policy can be used, or one of the system defined policies.
      order:
        description:
        - String specifying the vNIC assignment order (e.g., '1', '2').
        default: 'unspecified'
      state:
        description:
        - If C(present), will verify vnic is configured within policy.
          If C(absent), will verify vnic is absent from policy.
        choices: [ present, absent ]
        default: present
    version_added: '2.8'
  iscsi_vnic_list:
    description:
    - List of iSCSI vNICs used by the LAN Connectivity Policy.
    suboptions:
      name:
        description:
        - The name of the iSCSI vNIC.
        required: yes
      overlay_vnic:
        description:
        - The LAN vNIC associated with this iSCSI vNIC.
      iscsi_adapter_policy:
        description:
        - The iSCSI adapter policy associated with this iSCSI vNIC.
      mac_address:
        description:
        - The MAC address associated with this iSCSI vNIC.
        - If the MAC address is not set, Cisco UCS Manager uses a derived MAC address.
        default: derived
      vlan_name:
        description:
        - The VLAN used for the iSCSI vNIC.
        default: default
      state:
        description:
        - If C(present), will verify iscsi vnic is configured within policy.
          If C(absent), will verify iscsi vnic is absent from policy.
        choices: [ present, absent ]
        default: present
    version_added: '2.8'
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
    name: Cntr-FC-Boot
    vnic_list:
    - name: eno1
      vnic_template: Cntr-Template
      adapter_policy: Linux
    - name: eno2
      vnic_template: Container-NFS-A
      adapter_policy: Linux
    - name: eno3
      vnic_template: Container-NFS-B
      adapter_policy: Linux
    iscsi_vnic_list:
    - name: iSCSIa
      overlay_vnic: eno1
      iscsi_adapter_policy: default
      vlan_name: Container-MGMT-VLAN
    - name: iSCSIb
      overlay_vnic: eno3
      iscsi_adapter_policy: default
      vlan_name: Container-TNT-A-NFS

- name: Remove LAN Connectivity Policy
  ucs_lan_connectivity:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: Cntr-FC-Boot
    state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def configure_lan_connectivity(ucs, module, dn):
    from ucsmsdk.mometa.vnic.VnicLanConnPolicy import VnicLanConnPolicy
    from ucsmsdk.mometa.vnic.VnicEther import VnicEther
    from ucsmsdk.mometa.vnic.VnicIScsiLCP import VnicIScsiLCP
    from ucsmsdk.mometa.vnic.VnicVlan import VnicVlan

    if not module.check_mode:
        try:
            # create if mo does not already exist
            mo = VnicLanConnPolicy(
                parent_mo_or_dn=module.params['org_dn'],
                name=module.params['name'],
                descr=module.params['description'],
            )

            if module.params.get('vnic_list'):
                for vnic in module.params['vnic_list']:
                    if vnic['state'] == 'absent':
                        child_dn = dn + '/ether-' + vnic['name']
                        mo_1 = ucs.login_handle.query_dn(child_dn)
                        if mo_1:
                            ucs.login_handle.remove_mo(mo_1)
                    else:  # state == 'present'
                        mo_1 = VnicEther(
                            addr='derived',
                            parent_mo_or_dn=mo,
                            name=vnic['name'],
                            adaptor_profile_name=vnic['adapter_policy'],
                            nw_templ_name=vnic['vnic_template'],
                            order=vnic['order'],
                        )

            if module.params.get('iscsi_vnic_list'):
                for iscsi_vnic in module.params['iscsi_vnic_list']:
                    if iscsi_vnic['state'] == 'absent':
                        child_dn = dn + '/iscsi-' + iscsi_vnic['name']
                        mo_1 = ucs.login_handle.query_dn(child_dn)
                        if mo_1:
                            ucs.login_handle.remove_mo(mo_1)
                    else:  # state == 'present'
                        mo_1 = VnicIScsiLCP(
                            parent_mo_or_dn=mo,
                            name=iscsi_vnic['name'],
                            adaptor_profile_name=iscsi_vnic['iscsi_adapter_policy'],
                            vnic_name=iscsi_vnic['overlay_vnic'],
                            addr=iscsi_vnic['mac_address'],
                        )
                        VnicVlan(
                            parent_mo_or_dn=mo_1,
                            vlan_name=iscsi_vnic['vlan_name'],
                        )

            ucs.login_handle.add_mo(mo, True)
            ucs.login_handle.commit()
        except Exception as e:  # generic Exception handling because SDK can throw a variety of exceptions
            ucs.result['msg'] = "setup error: %s " % str(e)
            module.fail_json(**ucs.result)

    ucs.result['changed'] = True


def check_vnic_props(ucs, module, dn):
    props_match = True

    if module.params.get('vnic_list'):
        # check vnicEther props
        for vnic in module.params['vnic_list']:
            child_dn = dn + '/ether-' + vnic['name']
            mo_1 = ucs.login_handle.query_dn(child_dn)
            if mo_1:
                if vnic['state'] == 'absent':
                    props_match = False
                    break
                else:   # state == 'present'
                    kwargs = dict(adaptor_profile_name=vnic['adapter_policy'])
                    kwargs['order'] = vnic['order']
                    kwargs['nw_templ_name'] = vnic['vnic_template']
                    if not (mo_1.check_prop_match(**kwargs)):
                        props_match = False
                        break
            else:   # mo_1 did not exist
                if vnic['state'] == 'present':
                    props_match = False
                    break

    return props_match


def check_iscsi_vnic_props(ucs, module, dn):
    props_match = True

    if module.params.get('iscsi_vnic_list'):
        # check vnicIScsiLCP props
        for iscsi_vnic in module.params['iscsi_vnic_list']:
            child_dn = dn + '/iscsi-' + iscsi_vnic['name']
            mo_1 = ucs.login_handle.query_dn(child_dn)
            if mo_1:
                if iscsi_vnic['state'] == 'absent':
                    props_match = False
                    break
                else:   # state == 'present'
                    kwargs = dict(vnic_name=iscsi_vnic['overlay_vnic'])
                    kwargs['adaptor_profile_name'] = iscsi_vnic['iscsi_adapter_policy']
                    kwargs['addr'] = iscsi_vnic['mac_address']
                    if (mo_1.check_prop_match(**kwargs)):
                        # check vlan
                        child_dn = child_dn + '/vlan'
                        mo_2 = ucs.login_handle.query_dn(child_dn)
                        if mo_2:
                            kwargs = dict(vlan_name=iscsi_vnic['vlan_name'])
                            if not (mo_2.check_prop_match(**kwargs)):
                                props_match = False
                                break
                    else:   # mo_1 props did not match
                        props_match = False
                        break
            else:   # mo_1 did not exist
                if iscsi_vnic['state'] == 'present':
                    props_match = False
                    break

    return props_match


def check_lan_connecivity_props(ucs, module, mo, dn):
    props_match = False

    # check top-level mo props
    kwargs = dict(descr=module.params['description'])
    if (mo.check_prop_match(**kwargs)):
        # top-level props match, check next level mo/props
        # check vnic 1st
        props_match = check_vnic_props(ucs, module, dn)

        if props_match:
            props_match = check_iscsi_vnic_props(ucs, module, dn)

    return props_match


def main():
    vnic = dict(
        name=dict(type='str', required=True),
        vnic_template=dict(type='str', required=True),
        adapter_policy=dict(type='str', default=''),
        order=dict(type='str', default='unspecified'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    iscsi_vnic = dict(
        name=dict(type='str', required=True),
        overlay_vnic=dict(type='str', default=''),
        iscsi_adapter_policy=dict(type='str', default=''),
        mac_address=dict(type='str', default='derived'),
        vlan_name=dict(type='str', default='default'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_dn=dict(type='str', default='org-root'),
        name=dict(type='str', required=True),
        description=dict(type='str', aliases=['descr'], default=''),
        vnic_list=dict(type='list', elements='dict', options=vnic),
        iscsi_vnic_list=dict(type='list', elements='dict', options=iscsi_vnic),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )
    ucs = UCSModule(module)
    # UCSModule creation above verifies ucsmsdk is present and exits on failure.
    # Additional imports are done below or in called functions.

    ucs.result['changed'] = False
    props_match = False
    # dn is <org_dn>/lan-conn-pol-<name>
    dn = module.params['org_dn'] + '/lan-conn-pol-' + module.params['name']

    mo = ucs.login_handle.query_dn(dn)
    if mo:
        if module.params['state'] == 'absent':
            # mo must exist but all properties do not have to match
            if not module.check_mode:
                ucs.login_handle.remove_mo(mo)
                ucs.login_handle.commit()
            ucs.result['changed'] = True
        else:  # state == 'present'
            props_match = check_lan_connecivity_props(ucs, module, mo, dn)

    if module.params['state'] == 'present' and not props_match:
        configure_lan_connectivity(ucs, module, dn)

    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()

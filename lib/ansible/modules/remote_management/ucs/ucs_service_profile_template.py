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
module: ucs_service_profile_template
short_description: Configures Service Profile Templates on Cisco UCS Manager
description:
- Configures Service Profile Templates on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify Service Profile Templates are present and will create if needed.
    - If C(absent), will verify Service Profile Templates are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the service profile template.
    - This name can be between 2 and 32 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - This name must be unique across all service profiles and service profile templates within the same organization.
    required: yes
  template_type:
    description:
    - "The template type field which can be one of the following:"
    - "initial-template — Any service profiles created from this template are not updated if the template changes."
    - "updating-template — Any service profiles created from this template are updated if the template changes."
    choices: [initial-template, updating-template]
    default: initial-template
  uuid_pool:
    description:
    - Specifies how the UUID will be set on a server associated with a service profile created from this template.
    - "The uuid_pool option can be the name of the UUID pool to use or '' (the empty string)."
    - An empty string will use the UUID assigned to the server by the manufacturer, and the
    - UUID remains unassigned until a service profile created from this template is associated with a server. At that point,
    - the UUID is set to the UUID value assigned to the server by the manufacturer. If the service profile is later moved to
    - a different server, the UUID is changed to match the new server."
    default: default
  description:
    description:
    - A user-defined description of the service profile template.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
  storage_profile:
    description:
    - The name of the storage profile you want to associate with service profiles created from this template
  local_disk_policy:
    description:
    - The name of the local disk policy you want to associate with service profiles created from this template.
  lan_connectivity_policy:
    description:
    - The name of the LAN connectivity policy you want to associate with service profiles created from this template.
  iqn_pool:
    description:
    - The name of the IQN pool (initiator) you want to apply to all iSCSI vNICs for service profiles created from this template.
  san_connectivity_policy:
    description:
    - The name of the SAN connectivity policy you want to associate with service profiles created from this template.
  vmedia_policy:
    description:
    - The name of the vMedia policy you want to associate with service profiles created from this template.
  boot_policy:
    description:
    - The name of the boot order policy you want to associate with service profiles created from this template.
    default: default
  maintenance_policy:
    description:
    - The name of the maintenance policy you want to associate with service profiles created from this template.
  server_pool:
    description:
    - The name of the server pool you want to associate with this service profile template.
  server_pool_qualification:
    description:
    - The name of the server pool policy qualificaiton you want to use for this service profile template.
  power_state:
    description:
    - The power state to be applied when a service profile created from this template is associated with a server.
    choices: [up, down]
    default: up
  host_firmware_package:
    description:
    - The name of the host firmware package you want to associate with service profiles created from this template.
  bios_policy:
    description:
    - The name of the BIOS policy you want to associate with service profiles created from this template.
  ipmi_access_profile:
    description:
    - The name of the IPMI access profile you want to associate with service profiles created from this template.
  sol_policy:
    description:
    - The name of the Serial over LAN (SoL) policy you want to associate with service profiles created from this template.
  mgmt_ip_pool:
    description:
    - The name of the management IP pool you want to use with service profiles created from this template.
    default: ext-mgmt
  power_control_policy:
    description:
    - The name of the power control policy you want to associate with service profiles created from this template.
    default: default
  power_sync_policy:
    description:
    - The name of the power sync policy you want to associate with service profiles created from this template.
  scrub_policy:
    description:
    - The name of the scrub policy you want to associate with service profiles created from this template.
  kvm_mgmt_policy:
    description:
    - The name of the KVM management policy you want to associate with service profiles created from this template.
  graphics_card_policy:
    description:
    - The name of the graphics card policy you want to associate with service profiles created from this template.
  threshold_policy:
    description:
    - The name of the threshold policy you want to associate with service profiles created from this template.
    default: default
  user_label:
    description:
    - The User Label you want to assign to service profiles created from this template.
  mgmt_interface_mode:
    description:
    - The Management Interface you want to assign to service profiles created from this template.
    choices: ['', in-band]
  mgmt_vnet_name:
    description:
    - A VLAN selected from the associated VLAN group.
  mgmt_inband_pool_name:
    description:
    - How the inband management IPv4 address is derived for the server associated with this service profile.
  org_dn:
    description:
    - Org dn (distinguished name)
    default: org-root
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.8'
'''

EXAMPLES = r'''
- name: Configure Service Profile Template with LAN/SAN Connectivity and all other options defaulted
  ucs_service_profile_template:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: DEE-Ctrl
    template_type: updating-template
    uuid_pool: UUID-Pool
    storage_profile: DEE-StgProf
    lan_connectivity_policy: Cntr-FC-Boot
    iqn_pool: iSCSI-Boot-A
    san_connectivity_policy: Cntr-FC-Boot
    boot_policy: DEE-vMedia
    maintenance_policy: default
    server_pool: Container-Pool
    host_firmware_package: 3.1.2b
    bios_policy: Docker

- name: Remove Service Profile Template
  ucs_service_profile_template:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: DEE-Ctrl
    state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def configure_service_profile_template(ucs, module):
    from ucsmsdk.mometa.ls.LsServer import LsServer
    from ucsmsdk.mometa.vnic.VnicConnDef import VnicConnDef
    from ucsmsdk.mometa.vnic.VnicIScsiNode import VnicIScsiNode
    from ucsmsdk.mometa.ls.LsRequirement import LsRequirement
    from ucsmsdk.mometa.ls.LsPower import LsPower
    from ucsmsdk.mometa.lstorage.LstorageProfileBinding import LstorageProfileBinding
    from ucsmsdk.mometa.mgmt.MgmtInterface import MgmtInterface
    from ucsmsdk.mometa.mgmt.MgmtVnet import MgmtVnet
    from ucsmsdk.mometa.vnic.VnicIpV4MgmtPooledAddr import VnicIpV4MgmtPooledAddr

    if not module.check_mode:
        try:
            # create if mo does not already exist
            mo = LsServer(
                parent_mo_or_dn=module.params['org_dn'],
                bios_profile_name=module.params['bios_policy'],
                boot_policy_name=module.params['boot_policy'],
                descr=module.params['description'],
                ext_ip_state='pooled',
                ext_ip_pool_name=module.params['mgmt_ip_pool'],
                # graphics_card_policy_name=module.params['graphics_card_policy'],
                host_fw_policy_name=module.params['host_firmware_package'],
                ident_pool_name=module.params['uuid_pool'],
                kvm_mgmt_policy_name=module.params['kvm_mgmt_policy'],
                local_disk_policy_name=module.params['local_disk_policy'],
                maint_policy_name=module.params['maintenance_policy'],
                mgmt_access_policy_name=module.params['ipmi_access_profile'],
                name=module.params['name'],
                power_policy_name=module.params['power_control_policy'],
                power_sync_policy_name=module.params['power_sync_policy'],
                scrub_policy_name=module.params['scrub_policy'],
                sol_policy_name=module.params['sol_policy'],
                stats_policy_name=module.params['threshold_policy'],
                type=module.params['template_type'],
                usr_lbl=module.params['user_label'],
                vmedia_policy_name=module.params['vmedia_policy'],
            )

            if module.params['storage_profile']:
                # Storage profile
                mo_1 = LstorageProfileBinding(
                    parent_mo_or_dn=mo,
                    storage_profile_name=module.params['storage_profile'],
                )

            if module.params['mgmt_interface_mode']:
                # Management Interface
                mo_1 = MgmtInterface(
                    parent_mo_or_dn=mo,
                    mode=module.params['mgmt_interface_mode'],
                    ip_v4_state='pooled',
                )
                mo_2 = MgmtVnet(
                    parent_mo_or_dn=mo_1,
                    id='1',
                    name=module.params['mgmt_vnet_name'],
                )
                VnicIpV4MgmtPooledAddr(
                    parent_mo_or_dn=mo_2,
                    name=module.params['mgmt_inband_pool_name'],
                )

            # LAN/SAN connectivity policy
            mo_1 = VnicConnDef(
                parent_mo_or_dn=mo,
                lan_conn_policy_name=module.params['lan_connectivity_policy'],
                san_conn_policy_name=module.params['san_connectivity_policy'],
            )

            if module.params['iqn_pool']:
                # IQN pool
                mo_1 = VnicIScsiNode(
                    parent_mo_or_dn=mo,
                    iqn_ident_pool_name=module.params['iqn_pool']
                )

            # power state
            admin_state = 'admin-' + module.params['power_state']
            mo_1 = LsPower(
                parent_mo_or_dn=mo,
                state=admin_state,
            )

            if module.params['server_pool']:
                # server pool
                mo_1 = LsRequirement(
                    parent_mo_or_dn=mo,
                    name=module.params['server_pool'],
                    qualifier=module.params['server_pool_qualification'],
                )

            ucs.login_handle.add_mo(mo, True)
            ucs.login_handle.commit()
        except Exception as e:  # generic Exception handling because SDK can throw a variety of exceptions
            ucs.result['msg'] = "setup error: %s " % str(e)
            module.fail_json(**ucs.result)

    ucs.result['changed'] = True


def check_storage_profile_props(ucs, module, dn):
    props_match = False

    child_dn = dn + '/profile-binding'
    mo_1 = ucs.login_handle.query_dn(child_dn)
    if mo_1:
        kwargs = dict(storage_profile_name=module.params['storage_profile'])
        if mo_1.check_prop_match(**kwargs):
            props_match = True
    elif not module.params['storage_profile']:
        # no stroage profile mo or desired state
        props_match = True

    return props_match


def check_connectivity_policy_props(ucs, module, dn):
    props_match = False

    child_dn = dn + '/conn-def'
    mo_1 = ucs.login_handle.query_dn(child_dn)
    if mo_1:
        kwargs = dict(lan_conn_policy_name=module.params['lan_connectivity_policy'])
        kwargs['san_conn_policy_name'] = module.params['san_connectivity_policy']
        if mo_1.check_prop_match(**kwargs):
            props_match = True
    elif not module.params['lan_connectivity_policy'] and not module.params['san_connectivity_policy']:
        # no mo and no desired state
        props_match = True

    return props_match


def check_iqn_pool_props(ucs, module, dn):
    props_match = False

    child_dn = dn + '/iscsi-node'
    mo_1 = ucs.login_handle.query_dn(child_dn)
    if mo_1:
        kwargs = dict(iqn_ident_pool_name=module.params['iqn_pool'])
        if mo_1.check_prop_match(**kwargs):
            props_match = True
    elif not module.params['iqn_pool']:
        # no mo and no desired state
        props_match = True

    return props_match


def check_inband_management_props(ucs, module, dn):
    props_match = False

    child_dn = dn + '/iface-in-band'
    mo_1 = ucs.login_handle.query_dn(child_dn)
    if mo_1:
        kwargs = dict(mode=module.params['mgmt_interface_mode'])
        if mo_1.check_prop_match(**kwargs):
            child_dn = child_dn + '/network'
            mo_2 = ucs.login_handle.query_dn(child_dn)
            if mo_2:
                kwargs = dict(name=module.params['mgmt_vnet_name'])
                if mo_2.check_prop_match(**kwargs):
                    child_dn = child_dn + '/ipv4-pooled-addr'
                    mo_3 = ucs.login_handle.query_dn(child_dn)
                    if mo_3:
                        kwargs = dict(name=module.params['mgmt_inband_pool_name'])
                        if mo_3.check_prop_match(**kwargs):
                            props_match = True
    elif not module.params['mgmt_interface_mode']:
        # no mo and no desired state
        props_match = True

    return props_match


def check_power_props(ucs, module, dn):
    props_match = False

    child_dn = dn + '/power'
    mo_1 = ucs.login_handle.query_dn(child_dn)
    if mo_1:
        kwargs = dict(state=module.params['power_state'])
        if mo_1.check_prop_match(**kwargs):
            props_match = True
    elif not module.params['power_state']:
        # no mo and no desired state
        props_match = True

    return props_match


def check_server_pool(ucs, module, dn):
    props_match = False

    child_dn = dn + '/pn-req'
    mo_1 = ucs.login_handle.query_dn(child_dn)
    if mo_1:
        kwargs = dict(name=module.params['server_pool'])
        kwargs['qualifier'] = module.params['server_pool_qualification']
        if mo_1.check_prop_match(**kwargs):
            props_match = True
    elif not module.params['server_pool']:
        # no pn-req object and no server pool name provided
        props_match = True

    return props_match


def check_serivce_profile_templates_props(ucs, module, mo, dn):
    props_match = False

    # check top-level mo props
    kwargs = dict(bios_profile_name=module.params['bios_policy'])
    kwargs['boot_policy_name'] = module.params['boot_policy']
    kwargs['descr'] = module.params['description']
    kwargs['ext_ip_pool_name'] = module.params['mgmt_ip_pool']
    # kwargs['graphics_card_policy_name'] = module.params['graphics_card_policy']
    kwargs['host_fw_policy_name'] = module.params['host_firmware_package']
    kwargs['ident_pool_name'] = module.params['uuid_pool']
    kwargs['kvm_mgmt_policy_name'] = module.params['kvm_mgmt_policy']
    kwargs['local_disk_policy_name'] = module.params['local_disk_policy']
    kwargs['maint_policy_name'] = module.params['maintenance_policy']
    kwargs['mgmt_access_policy_name'] = module.params['ipmi_access_profile']
    kwargs['power_policy_name'] = module.params['power_control_policy']
    kwargs['power_sync_policy_name'] = module.params['power_sync_policy']
    kwargs['scrub_policy_name'] = module.params['scrub_policy']
    kwargs['sol_policy_name'] = module.params['sol_policy']
    kwargs['stats_policy_name'] = module.params['threshold_policy']
    kwargs['type'] = module.params['template_type']
    kwargs['usr_lbl'] = module.params['user_label']
    kwargs['vmedia_policy_name'] = module.params['vmedia_policy']

    if mo.check_prop_match(**kwargs):
        # top-level props match, check next level mo/props
        # code below should discontinue checks once any mismatch is found

        # check storage profile 1st
        props_match = check_storage_profile_props(ucs, module, dn)

        if props_match:
            props_match = check_connectivity_policy_props(ucs, module, dn)

        if props_match:
            props_match = check_iqn_pool_props(ucs, module, dn)

        if props_match:
            props_match = check_inband_management_props(ucs, module, dn)

        if props_match:
            props_match = check_power_props(ucs, module, dn)

        if props_match:
            props_match = check_server_pool(ucs, module, dn)

    return props_match


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_dn=dict(type='str', default='org-root'),
        name=dict(type='str', required=True),
        bios_policy=dict(type='str', default=''),
        boot_policy=dict(type='str', default='default'),
        description=dict(type='str', aliases=['descr'], default=''),
        mgmt_ip_pool=dict(type='str', default='ext-mgmt'),
        graphics_card_policy=dict(type='str', default=''),
        host_firmware_package=dict(type='str', default=''),
        uuid_pool=dict(type='str', default='default'),
        kvm_mgmt_policy=dict(type='str', default=''),
        local_disk_policy=dict(type='str', default=''),
        maintenance_policy=dict(type='str', default=''),
        ipmi_access_profile=dict(type='str', default=''),
        power_control_policy=dict(type='str', default='default'),
        power_sync_policy=dict(type='str', default=''),
        scrub_policy=dict(type='str', default=''),
        sol_policy=dict(type='str', default=''),
        threshold_policy=dict(type='str', default='default'),
        template_type=dict(type='str', default='initial-template', choices=['initial-template', 'updating-template']),
        user_label=dict(type='str', default=''),
        vmedia_policy=dict(type='str', default=''),
        storage_profile=dict(type='str', default=''),
        lan_connectivity_policy=dict(type='str', default=''),
        iqn_pool=dict(type='str', default=''),
        san_connectivity_policy=dict(type='str', default=''),
        server_pool=dict(type='str', default=''),
        server_pool_qualification=dict(type='str', default=''),
        power_state=dict(type='str', default='up', choices=['up', 'down']),
        mgmt_interface_mode=dict(type='str', default='', choices=['', 'in-band']),
        mgmt_vnet_name=dict(type='str', default=''),
        mgmt_inband_pool_name=dict(type='str', default=''),
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
    # dn is <org_dn>/ls-<name>
    dn = module.params['org_dn'] + '/ls-' + module.params['name']

    mo = ucs.login_handle.query_dn(dn)
    if mo:
        if module.params['state'] == 'absent':
            # mo must exist but all properties do not have to match
            if not module.check_mode:
                ucs.login_handle.remove_mo(mo)
                ucs.login_handle.commit()
            ucs.result['changed'] = True
        else:  # state == 'present'
            props_match = check_serivce_profile_templates_props(ucs, module, mo, dn)

    if module.params['state'] == 'present' and not props_match:
        configure_service_profile_template(ucs, module)

    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()

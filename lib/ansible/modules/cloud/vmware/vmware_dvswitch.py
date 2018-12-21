#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
# Copyright: (c) 2018, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_dvswitch
short_description: Create or remove a Distributed Switch
description:
    - This module can be used to create, remove a Distributed Switch.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
    - Tested on vSphere 6.5 and 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter_name:
        description:
            - The name of the datacenter that will contain the Distributed Switch.
        required: True
        aliases: ['datacenter']
    switch_name:
        description:
        - The name of the distribute vSwitch to create or remove.
        required: True
        aliases: ['switch', 'dvswitch']
    switch_version:
        description:
            - The version of the Distributed Switch to create.
            - Can be 6.0.0, 5.5.0, 5.1.0, 5.0.0 with a vCenter running vSphere 6.0 and 6.5.
            - Can be 6.6.0, 6.5.0, 6.0.0 with a vCenter running vSphere 6.7.
            - The version must macht the version of the ESXi hosts you want to connect.
            - The version of the vCenter server is used if not specified.
            - Required only if C(state) is set to C(present).
        version_added: 2.5
        choices: ['5.0.0', '5.1.0', '5.5.0', '6.0.0', '6.5.0', '6.6.0']
        aliases: ['version']
    mtu:
        description:
            - The switch maximum transmission unit.
            - Required parameter for C(state) both C(present) and C(absent), before Ansible 2.6 version.
            - Required only if C(state) is set to C(present), for Ansible 2.6 and onwards.
            - Accepts value between 1280 to 9000 (both inclusive).
        type: int
        default: 1500
    multicast_filtering_mode:
        description:
            - The multicast filtering mode.
            - 'C(basic) mode: multicast traffic for virtual machines is forwarded according to the destination MAC address of the multicast group.'
            - 'C(snooping) mode: the Distributed Switch provides IGMP and MLD snooping according to RFC 4541.'
        type: str
        choices: ['basic', 'snooping']
        default: 'basic'
        version_added: 2.8
    uplink_quantity:
        description:
            - Quantity of uplink per ESXi host added to the Distributed Switch.
            - The uplink quantity can be increased or decreased, but a decrease will only be successfull if the uplink isn't used by a portgroup.
            - Required parameter for C(state) both C(present) and C(absent), before Ansible 2.6 version.
            - Required only if C(state) is set to C(present), for Ansible 2.6 and onwards.
    uplink_prefix:
        description:
            - The prefix used for the naming of the uplinks.
            - Only valid if the Distributed Switch will be created. Not used if the Distributed Switch is already present.
            - Uplinks are created as Uplink 1, Uplink 2, etc. pp. by default.
        default: 'Uplink '
        version_added: 2.8
    discovery_proto:
        description:
            - Link discovery protocol between Cisco and Link Layer discovery.
            - Required parameter for C(state) both C(present) and C(absent), before Ansible 2.6 version.
            - Required only if C(state) is set to C(present), for Ansible 2.6 and onwards.
            - 'C(cdp): Use Cisco Discovery Protocol (CDP).'
            - 'C(lldp): Use Link Layer Discovery Protocol (LLDP).'
            - 'C(disabled): Do not use a discovery protocol.'
        choices: ['cdp', 'lldp', 'disabled']
        default: 'cdp'
        aliases: ['discovery_protocol']
    discovery_operation:
        description:
            - Select the discovery operation.
            - Required parameter for C(state) both C(present) and C(absent), before Ansible 2.6 version.
            - Required only if C(state) is set to C(present), for Ansible 2.6 and onwards.
        choices: ['both', 'advertise', 'listen']
        default: 'listen'
    contact:
        description:
            - Dictionary which configures administrtor contact name and description for the Distributed Switch.
            - 'Valid attributes are:'
            - '- C(name) (str): Administrator name.'
            - '- C(description) (str): Description or other details.'
        type: dict
        version_added: 2.8
    description:
        description:
            - Description of the Distributed Switch.
        type: str
        version_added: 2.8
    health_check:
        description:
            - Dictionary which configures Health Check for the Distributed Switch.
            - 'Valid attributes are:'
            - '- C(vlan_mtu) (bool): VLAN and MTU health check. (default: False)'
            - '- C(teaming_failover) (bool): Teaming and failover health check. (default: False)'
            - '- C(vlan_mtu_interval) (int): VLAN and MTU health check interval (minutes). (default: 0)'
            - '- The default for C(vlan_mtu_interval) is 1 in the vSphere Client if the VLAN and MTU health check is enabled.'
            - '- C(teaming_failover_interval) (int): Teaming and failover health check interval (minutes). (default: 0)'
            - '- The default for C(teaming_failover_interval) is 1 in the vSphere Client if the Teaming and failover health check is enabled.'
        type: dict
        default: {
            vlan_mtu: False,
            teaming_failover: False,
            vlan_mtu_interval: 0,
            teaming_failover_interval: 0,
        }
        version_added: 2.8
    state:
        description:
            - If set to C(present) and the Distributed Switch doesn't exists then the Distributed Switch will be created.
            - If set to C(absent) and the Distributed Switch exists then the Distributed Switch will be deleted.
        default: 'present'
        choices: ['present', 'absent']
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Create dvSwitch
  vmware_dvswitch:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: '{{ datacenter }}'
    switch: dvSwitch
    version: 6.0.0
    mtu: 9000
    uplink_quantity: 2
    discovery_protocol: lldp
    discovery_operation: both
    state: present
  delegate_to: localhost

- name: Create dvSwitch with all options
  vmware_dvswitch:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: '{{ datacenter }}'
    switch: dvSwitch
    version: 6.5.0
    mtu: 9000
    uplink_quantity: 2
    uplink_prefix: 'Uplink_'
    discovery_protocol: cdp
    discovery_operation: both
    multicast_filtering_mode: snooping
    health_check:
      vlan_mtu: true
      vlan_mtu_interval: 1
      teaming_failover: true
      teaming_failover_interval: 1
    state: present
  delegate_to: localhost

- name: Delete dvSwitch
  vmware_dvswitch:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: '{{ datacenter }}'
    switch: dvSwitch
    state: absent
  delegate_to: localhost
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: str
    sample: {
        "changed": false,
        "contact": null,
        "contact_details": null,
        "description": null,
        "discovery_operation": "both",
        "discovery_protocol": "cdp",
        "dvswitch": "test",
        "health_check_teaming": false,
        "health_check_teaming_interval": 0,
        "health_check_vlan": false,
        "health_check_vlan_interval": 0,
        "mtu": 9000,
        "multicast_filtering_mode": "basic",
        "result": "DVS already configured properly",
        "uplink_quantity": 2,
        "uplinks": [
            "Uplink_1",
            "Uplink_2"
        ],
        "version": "6.6.0"
    }
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (
    PyVmomi, find_datacenter_by_name, TaskError, find_dvs_by_name, vmware_argument_spec, wait_for_task
)


class VMwareDvSwitch(PyVmomi):
    """Class to manage a Distributed Virtual Switch"""
    def __init__(self, module):
        super(VMwareDvSwitch, self).__init__(module)
        self.dvs = None
        self.datacenter = None
        self.switch_name = self.module.params['switch_name']
        self.switch_version = self.module.params['switch_version']
        if self.content.about.version == '6.7.0':
            self.vcenter_switch_version = '6.6.0'
        else:
            self.vcenter_switch_version = self.content.about.version
        self.datacenter_name = self.module.params['datacenter_name']
        self.mtu = self.module.params['mtu']
        # MTU sanity check
        if not 1280 <= self.mtu <= 9000:
            self.module.fail_json(
                msg="MTU value should be between 1280 and 9000 (both inclusive), provided %d." % self.mtu
            )
        self.multicast_filtering_mode = self.module.params['multicast_filtering_mode']
        self.uplink_quantity = self.module.params['uplink_quantity']
        self.uplink_prefix = self.module.params['uplink_prefix']
        self.discovery_protocol = self.module.params['discovery_proto']
        self.discovery_operation = self.module.params['discovery_operation']
        # TODO: add port mirroring
        self.health_check_vlan = self.params['health_check'].get('vlan_mtu')
        self.health_check_vlan_interval = self.params['health_check'].get('vlan_mtu_interval')
        self.health_check_teaming = self.params['health_check'].get('teaming_failover')
        self.health_check_teaming_interval = self.params['health_check'].get('teaming_failover_interval')
        if self.params['contact']:
            self.contact_name = self.params['contact'].get('name')
            self.contact_details = self.params['contact'].get('details')
        else:
            self.contact_name = None
            self.contact_details = None
        self.description = self.module.params['description']
        self.state = self.module.params['state']

    def process_state(self):
        """Process the current state of the DVS"""
        dvs_states = {
            'absent': {
                'present': self.destroy_dvswitch,
                'absent': self.exit_unchanged,
            },
            'present': {
                'present': self.update_dvswitch,
                'absent': self.create_dvswitch,
            }
        }

        try:
            dvs_states[self.state][self.check_dvs()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def check_dvs(self):
        """Check if DVS is present"""
        datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
        if datacenter is None:
            self.module.fail_json(msg="Failed to find datacenter %s" % self.datacenter_name)
        else:
            self.datacenter = datacenter
        self.dvs = find_dvs_by_name(self.content, self.switch_name)
        if self.dvs is None:
            return 'absent'
        return 'present'

    def create_dvswitch(self):
        """Create a DVS"""
        changed = True
        results = dict(changed=changed)

        spec = vim.DistributedVirtualSwitch.CreateSpec()
        spec.configSpec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
        # Name
        results['dvswitch'] = self.switch_name
        spec.configSpec.name = self.switch_name
        # MTU
        results['mtu'] = self.mtu
        spec.configSpec.maxMtu = self.mtu
        # Discovery Protocol type and operation
        results['discovery_protocol'] = self.discovery_protocol
        results['discovery_operation'] = self.discovery_operation
        spec.configSpec.linkDiscoveryProtocolConfig = self.create_ldp_spec()
        # Administrator contact
        results['contact'] = self.contact_name
        results['contact_details'] = self.contact_details
        if self.contact_name or self.contact_details:
            spec.contact = self.create_contact_spec()
        # Description
        results['description'] = self.description
        if self.description:
            spec.description = self.description
        # Uplinks
        results['uplink_quantity'] = self.uplink_quantity
        spec.configSpec.uplinkPortPolicy = vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy()
        for count in range(1, self.uplink_quantity + 1):
            spec.configSpec.uplinkPortPolicy.uplinkPortName.append("%s%d" % (self.uplink_prefix, count))
        results['uplinks'] = spec.configSpec.uplinkPortPolicy.uplinkPortName
        # Version
        results['version'] = self.switch_version
        if self.switch_version:
            spec.productInfo = self.create_product_spec(self.switch_version)

        if self.module.check_mode:
            result = "DVS would be created"
        else:
            # Create DVS
            network_folder = self.datacenter.networkFolder
            task = network_folder.CreateDVS_Task(spec)
            try:
                wait_for_task(task)
            except TaskError as invalid_argument:
                self.module.fail_json(
                    msg="Failed to create DVS : %s" % to_native(invalid_argument)
                )
            # Find new DVS
            self.dvs = find_dvs_by_name(self.content, self.switch_name)
            changed_multicast = False
            spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
            # Use the same version in the new spec; The version will be increased by one by the API automatically
            spec.configVersion = self.dvs.config.configVersion
            # Set multicast filtering mode
            results['multicast_filtering_mode'] = self.multicast_filtering_mode
            multicast_filtering_mode = self.get_api_mc_filtering_mode(self.multicast_filtering_mode)
            if self.dvs.config.multicastFilteringMode != multicast_filtering_mode:
                changed_multicast = True
                spec.multicastFilteringMode = multicast_filtering_mode
            spec.multicastFilteringMode = self.get_api_mc_filtering_mode(self.multicast_filtering_mode)
            if changed_multicast:
                self.update_dvs_config(self.dvs, spec)
            # Set Health Check config
            results['health_check_vlan'] = self.health_check_vlan
            results['health_check_teaming'] = self.health_check_teaming
            result = self.check_health_check_config(self.dvs.config.healthCheckConfig)
            changed_health_check = result[1]
            if changed_health_check:
                self.update_health_check_config(self.dvs, result[0])
            result = "DVS created"
        self.module.exit_json(changed=changed, result=to_native(result))

    def create_ldp_spec(self):
        """Create Link Discovery Protocol config spec"""
        ldp_config_spec = vim.host.LinkDiscoveryProtocolConfig()
        if self.discovery_protocol == 'disabled':
            ldp_config_spec.protocol = 'cdp'
            ldp_config_spec.operation = 'none'
        else:
            ldp_config_spec.protocol = self.discovery_protocol
            ldp_config_spec.operation = self.discovery_operation
        return ldp_config_spec

    def create_product_spec(self, switch_version):
        """Create product info spec"""
        product_info_spec = vim.dvs.ProductSpec()
        product_info_spec.version = switch_version
        return product_info_spec

    @staticmethod
    def get_api_mc_filtering_mode(mode):
        """Get Multicast filtering mode"""
        if mode == 'basic':
            return 'legacyFiltering'
        return 'snooping'

    def create_contact_spec(self):
        """Create contact info spec"""
        contact_info_spec = vim.DistributedVirtualSwitch.ContactInfo()
        contact_info_spec.name = self.contact_name
        contact_info_spec.contact = self.contact_details
        return contact_info_spec

    def update_dvs_config(self, switch_object, spec):
        """Update DVS config"""
        try:
            task = switch_object.ReconfigureDvs_Task(spec)
            wait_for_task(task)
        except TaskError as invalid_argument:
            self.module.fail_json(
                msg="Failed to update DVS : %s" % to_native(invalid_argument)
            )

    def check_health_check_config(self, health_check_config):
        """Check Health Check config"""
        changed = changed_vlan = changed_vlan_interval = changed_teaming = changed_teaming_interval = False
        vlan_previous = teaming_previous = None
        vlan_interval_previous = teaming_interval_previous = 0
        for config in health_check_config:
            if isinstance(config, vim.dvs.VmwareDistributedVirtualSwitch.VlanMtuHealthCheckConfig):
                if config.enable != self.health_check_vlan:
                    changed = changed_vlan = True
                    vlan_previous = config.enable
                    config.enable = self.health_check_vlan
                if config.enable and config.interval != self.health_check_vlan_interval:
                    changed = changed_vlan_interval = True
                    vlan_interval_previous = config.interval
                    config.interval = self.health_check_vlan_interval
            if isinstance(config, vim.dvs.VmwareDistributedVirtualSwitch.TeamingHealthCheckConfig):
                if config.enable != self.health_check_teaming:
                    changed = changed_teaming = True
                    teaming_previous = config.enable
                    config.enable = self.health_check_teaming
                if config.enable and config.interval != self.health_check_teaming_interval:
                    changed = changed_teaming_interval = True
                    teaming_interval_previous = config.interval
                    config.interval = self.health_check_teaming_interval
        return (health_check_config, changed, changed_vlan, vlan_previous, changed_vlan_interval, vlan_interval_previous,
                changed_teaming, teaming_previous, changed_teaming_interval, teaming_interval_previous)

    def update_health_check_config(self, switch_object, health_check_config):
        """Update Health Check config"""
        try:
            task = switch_object.UpdateDVSHealthCheckConfig_Task(healthCheckConfig=health_check_config)
        except vim.fault.DvsFault as dvs_fault:
            self.module.fail_json(msg="Update failed due to DVS fault : %s" % to_native(dvs_fault))
        except vmodl.fault.NotSupported as not_supported:
            self.module.fail_json(msg="Health check not supported on the switch : %s" % to_native(not_supported))
        except TaskError as invalid_argument:
            self.module.fail_json(msg="Failed to configure health check : %s" % to_native(invalid_argument))
        try:
            wait_for_task(task)
        except TaskError as invalid_argument:
            self.module.fail_json(msg="Failed to update health check config : %s" % to_native(invalid_argument))

    def exit_unchanged(self):
        """Exit with status message"""
        changed = False
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        results['result'] = "DVS not present"
        self.module.exit_json(**results)

    def destroy_dvswitch(self):
        """Delete a DVS"""
        changed = True
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        if self.module.check_mode:
            results['result'] = "DVS would be deleted"
        else:
            try:
                task = self.dvs.Destroy_Task()
            except vim.fault.VimFault as vim_fault:
                self.module.fail_json(msg="Failed to deleted DVS : %s" % to_native(vim_fault))
            wait_for_task(task)
            results['result'] = "DVS deleted"
        self.module.exit_json(**results)

    def update_dvswitch(self):
        """Check and update DVS settings"""
        changed = changed_settings = changed_ldp = changed_version = changed_health_check = False
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        changed_list = []

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
        # Use the same version in the new spec; The version will be increased by one by the API automatically
        config_spec.configVersion = self.dvs.config.configVersion

        # Check MTU
        results['mtu'] = self.mtu
        if self.dvs.config.maxMtu != self.mtu:
            changed = changed_settings = True
            changed_list.append("mtu")
            results['mtu_previous'] = config_spec.maxMtu
            config_spec.maxMtu = self.mtu

        # Check Discovery Protocol type and operation
        ldp_protocol = self.dvs.config.linkDiscoveryProtocolConfig.protocol
        ldp_operation = self.dvs.config.linkDiscoveryProtocolConfig.operation
        if self.discovery_protocol == 'disabled':
            results['discovery_protocol'] = self.discovery_protocol
            results['discovery_operation'] = 'n/a'
            if ldp_protocol != 'cdp' or ldp_operation != 'none':
                changed_ldp = True
                results['discovery_protocol_previous'] = ldp_protocol
                results['discovery_operation_previous'] = ldp_operation
        else:
            results['discovery_protocol'] = self.discovery_protocol
            results['discovery_operation'] = self.discovery_operation
            if ldp_protocol != self.discovery_protocol or ldp_operation != self.discovery_operation:
                changed_ldp = True
                if ldp_protocol != self.discovery_protocol:
                    results['discovery_protocol_previous'] = ldp_protocol
                if ldp_operation != self.discovery_operation:
                    results['discovery_operation_previous'] = ldp_operation
        if changed_ldp:
            changed = changed_settings = True
            changed_list.append("discovery protocol")
            config_spec.linkDiscoveryProtocolConfig = self.create_ldp_spec()

        # Check Multicast filtering mode
        results['multicast_filtering_mode'] = self.multicast_filtering_mode
        multicast_filtering_mode = self.get_api_mc_filtering_mode(self.multicast_filtering_mode)
        if self.dvs.config.multicastFilteringMode != multicast_filtering_mode:
            changed = changed_settings = True
            changed_list.append("multicast filtering")
            results['multicast_filtering_mode_previous'] = self.dvs.config.multicastFilteringMode
            config_spec.multicastFilteringMode = multicast_filtering_mode

        # Check administrator contact
        results['contact'] = self.contact_name
        results['contact_details'] = self.contact_details
        if self.dvs.config.contact.name != self.contact_name or self.dvs.config.contact.contact != self.contact_details:
            changed = changed_settings = True
            changed_list.append("contact")
            results['contact_previous'] = self.dvs.config.contact.name
            results['contact_details_previous'] = self.dvs.config.contact.contact
            config_spec.contact = self.create_contact_spec()

        # Check description
        results['description'] = self.description
        if self.dvs.config.description != self.description:
            changed = changed_settings = True
            changed_list.append("description")
            results['description_previous'] = self.dvs.config.description
            if self.description is None:
                # need to use empty string; will be set to None by API
                config_spec.description = ''
            else:
                config_spec.description = self.description

        # Check uplinks
        results['uplink_quantity'] = self.uplink_quantity
        if len(self.dvs.config.uplinkPortPolicy.uplinkPortName) != self.uplink_quantity:
            changed = changed_settings = True
            changed_list.append("uplink quantity")
            results['uplink_quantity_previous'] = len(self.dvs.config.uplinkPortPolicy.uplinkPortName)
            config_spec.uplinkPortPolicy = vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy()
            # just replace the uplink array if uplinks need to be added
            if len(self.dvs.config.uplinkPortPolicy.uplinkPortName) < self.uplink_quantity:
                for count in range(1, self.uplink_quantity + 1):
                    config_spec.uplinkPortPolicy.uplinkPortName.append("%s%d" % (self.uplink_prefix, count))
            # just replace the uplink array if uplinks need to be removed
            if len(self.dvs.config.uplinkPortPolicy.uplinkPortName) > self.uplink_quantity:
                for count in range(1, self.uplink_quantity + 1):
                    config_spec.uplinkPortPolicy.uplinkPortName.append("%s%d" % (self.uplink_prefix, count))
            results['uplinks'] = config_spec.uplinkPortPolicy.uplinkPortName
            results['uplinks_previous'] = self.dvs.config.uplinkPortPolicy.uplinkPortName
        else:
            # No uplink name check; uplink names can't be changed easily if they are used by a portgroup
            results['uplinks'] = self.dvs.config.uplinkPortPolicy.uplinkPortName

        # Check Health Check
        results['health_check_vlan'] = self.health_check_vlan
        results['health_check_teaming'] = self.health_check_teaming
        results['health_check_vlan_interval'] = self.health_check_vlan_interval
        results['health_check_teaming_interval'] = self.health_check_teaming_interval
        (health_check_config, changed_health_check, changed_vlan, vlan_previous,
         changed_vlan_interval, vlan_interval_previous, changed_teaming, teaming_previous,
         changed_teaming_interval, teaming_interval_previous) = \
            self.check_health_check_config(self.dvs.config.healthCheckConfig)
        if changed_health_check:
            changed = True
            changed_list.append("health check")
            if changed_vlan:
                results['health_check_vlan_previous'] = vlan_previous
            if changed_vlan_interval:
                results['health_check_vlan_interval_previous'] = vlan_interval_previous
            if changed_teaming:
                results['health_check_teaming_previous'] = teaming_previous
            if changed_teaming_interval:
                results['health_check_teaming_interval_previous'] = teaming_interval_previous

        # Check switch version
        if self.switch_version:
            results['version'] = self.switch_version
            if self.dvs.config.productInfo.version != self.switch_version:
                changed_version = True
                spec_product = self.create_product_spec(self.switch_version)
        else:
            results['version'] = self.vcenter_switch_version
            if self.dvs.config.productInfo.version != self.vcenter_switch_version:
                changed_version = True
                spec_product = self.create_product_spec(self.vcenter_switch_version)
        if changed_version:
            changed = True
            changed_list.append("switch version")
            results['version_previous'] = self.dvs.config.productInfo.version

        if changed:
            if self.module.check_mode:
                changed_suffix = ' would be changed'
            else:
                changed_suffix = ' changed'
            if len(changed_list) > 2:
                message = ', '.join(changed_list[:-1]) + ', and ' + str(changed_list[-1])
            elif len(changed_list) == 2:
                message = ' and '.join(changed_list)
            elif len(changed_list) == 1:
                message = changed_list[0]
            message += changed_suffix
            if not self.module.check_mode:
                if changed_settings:
                    self.update_dvs_config(self.dvs, config_spec)
                if changed_health_check:
                    self.update_health_check_config(self.dvs, health_check_config)
                if changed_version:
                    task = self.dvs.PerformDvsProductSpecOperation_Task("upgrade", spec_product)
                    try:
                        wait_for_task(task)
                    except TaskError as invalid_argument:
                        self.module.fail_json(msg="Failed to update DVS version : %s" % to_native(invalid_argument))
        else:
            message = "DVS already configured properly"
        results['changed'] = changed
        results['result'] = message

        self.module.exit_json(**results)


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            datacenter_name=dict(required=True, aliases=['datacenter']),
            switch_name=dict(required=True, aliases=['switch', 'dvswitch']),
            mtu=dict(type='int', default=1500),
            multicast_filtering_mode=dict(type='str', default='basic', choices=['basic', 'snooping']),
            switch_version=dict(
                choices=['5.0.0', '5.1.0', '5.5.0', '6.0.0', '6.5.0', '6.6.0'],
                aliases=['version'],
                default=None
            ),
            uplink_quantity=dict(type='int'),
            uplink_prefix=dict(type='str', default='Uplink '),
            discovery_proto=dict(
                type='str', choices=['cdp', 'lldp', 'disabled'], default='cdp', aliases=['discovery_protocol']
            ),
            discovery_operation=dict(type='str', choices=['both', 'advertise', 'listen'], default='listen'),
            health_check=dict(
                type='dict',
                options=dict(
                    vlan_mtu=dict(type='bool', default=False),
                    teaming_failover=dict(type='bool', default=False),
                    vlan_mtu_interval=dict(type='int', default=0),
                    teaming_failover_interval=dict(type='int', default=0),
                ),
                default=dict(
                    vlan_mtu=False,
                    teaming_failover=False,
                    vlan_mtu_interval=0,
                    teaming_failover_interval=0,
                ),
            ),
            contact=dict(
                type='dict',
                options=dict(
                    name=dict(type='str'),
                    description=dict(type='str'),
                ),
            ),
            description=dict(type='str'),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present',
             ['uplink_quantity']),
        ],
        supports_check_mode=True,
    )

    vmware_dvswitch = VMwareDvSwitch(module)
    vmware_dvswitch.process_state()


if __name__ == '__main__':
    main()

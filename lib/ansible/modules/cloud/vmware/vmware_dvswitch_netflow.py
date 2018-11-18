#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
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
module: vmware_dvswitch_netflow
short_description: Manage NetFlow configuration of a Distributed Switch
description:
    - This module can be used to configure NetFlow on a Distributed Switch.
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
    - Tested on vSphere 6.5 and 6.7
    - The switch IP can't be set in the current implementation.
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch:
        description:
            - The name of the Distributed Switch.
        type: str
        required: True
        aliases: ['dvswitch']
    collector_ip:
        description:
            - IPv4 or IPv6 address for the Netflow collector.
        type: str
        default: ''
    collector_port:
        description:
            - Port for the Netflow collector.
        type: int
        default: 0
    observation_domain:
        description:
            - The observation domain ID for the Netflow collector.
        type: int
        default: 0
    active_flow_export_timeout:
        description:
            - The number of seconds after which active flows are forced to be exported to the collector.
            - The allowed range is 60 to 3600.
        type: int
        default: 60
    idle_flow_export_timeout:
        description:
            - The number of seconds after which idle flows are forced to be exported to the collector.
            - The allowed range is 10 to 600.
        type: int
        default: 15
    sampling_rate:
        description:
            - The ratio of total number of packets to the number of packets analyzed.
            - The maximum value is 1000, which indicates an analysis rate of 0.001%. The value 0 indicates that the switch should analyze all packets.
        type: int
        default: 0
    process_internal_flows_only:
        description:
            - Whether to limit analysis to traffic that has both source and destination served by the same host.
        type: bool
        default: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: vCenter | Configure NetFlow on Distributed Switch(es)
  tags: dvswitch, dvswitch_netflow
  vmware_dvswitch_netflow:
    hostname: '{{ inventory_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch: dvSwitch
    collector_ip: 192.168.0.2
    collector_port: 1024
    observation_domain: 1
    active_flow_export_timeout: 61
    idle_flow_export_timeout: 16
    sampling_rate: 2
    process_internal_flows_only: True
    validate_certs: "{{ validate_vcenter_certs }}"
  delegate_to: localhost
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: string
    sample: {
        "active_flow_export_timeout": 61,
        "active_flow_export_timeout_previous": 60,
        "changed": true,
        "collector_ip": "192.168.0.2",
        "collector_ip_previous": "",
        "collector_port": 1024,
        "collector_port_previous": 0,
        "dvswitch": "dvSwitch",
        "idle_flow_export_timeout": 16,
        "idle_flow_export_timeout_previous": 15,
        "observation_domain": 1,
        "observation_domain_previous": 0,
        "process_internal_flows_only": true,
        "process_internal_flows_only_previous": false,
        "result": "collector IP address, collector port, and observation domain ID changed",
        "sampling_rate": 2,
        "sampling_rate_previous": 0
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (
    PyVmomi, TaskError, find_dvs_by_name, vmware_argument_spec, wait_for_task
)


class VMwareDvSwitchNetFlow(PyVmomi):
    """Class to manage NetFlow configuration of a Distributed Virtual Switch"""

    def __init__(self, module):
        super(VMwareDvSwitchNetFlow, self).__init__(module)
        self.switch_name = self.module.params['switch']
        self.netflow_collector_ip = self.params['collector_ip']
        self.netflow_collector_port = self.params['collector_port']
        self.netflow_observation_domain = self.params['observation_domain']
        # self.netflow_switch_ip = self.params['switch_ip']
        self.netflow_active_flow_export = self.params['active_flow_export_timeout']
        self.netflow_idle_flow_export = self.params['idle_flow_export_timeout']
        self.netflow_sampling_rate = self.params['sampling_rate']
        self.netflow_process_internal_flows = self.params['process_internal_flows_only']
        self.dvs = find_dvs_by_name(self.content, self.switch_name)
        if self.dvs is None:
            self.module.fail_json(msg="Failed to find DVS %s" % self.switch_name)

    def ensure(self):
        """Manage NetFlow configuration"""
        changed = False
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        changed_list = []

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
        # Use the same version in the new spec; The version will be increased by one by the API automatically
        config_spec.configVersion = self.dvs.config.configVersion

        # Check NetFlow
        results['collector_ip'] = self.netflow_collector_ip
        results['collector_port'] = self.netflow_collector_port
        results['observation_domain'] = self.netflow_observation_domain
        # results['switch_ip'] = self.netflow_switch_ip
        results['active_flow_export_timeout'] = self.netflow_active_flow_export
        results['idle_flow_export_timeout'] = self.netflow_idle_flow_export
        results['sampling_rate'] = self.netflow_sampling_rate
        results['process_internal_flows_only'] = self.netflow_process_internal_flows
        netflow_config = self.dvs.config.ipfixConfig
        netflow_config_spec = vim.dvs.VmwareDistributedVirtualSwitch.IpfixConfig()
        netflow_config_spec.collectorIpAddress = self.netflow_collector_ip
        netflow_config_spec.collectorPort = self.netflow_collector_port
        netflow_config_spec.observationDomainId = self.netflow_observation_domain
        netflow_config_spec.activeFlowTimeout = self.netflow_active_flow_export
        netflow_config_spec.idleFlowTimeout = self.netflow_idle_flow_export
        netflow_config_spec.samplingRate = self.netflow_sampling_rate
        netflow_config_spec.internalFlowsOnly = self.netflow_process_internal_flows
        # the collectorIpAddress can be '' or None
        if not (self.netflow_collector_ip == ''
                and (netflow_config.collectorIpAddress == '' or netflow_config.collectorIpAddress is None)):
            if netflow_config.collectorIpAddress != self.netflow_collector_ip:
                changed = True
                changed_list.append("collector IP address")
                results['collector_ip_previous'] = netflow_config.collectorIpAddress
        if netflow_config.collectorPort != self.netflow_collector_port:
            changed = True
            changed_list.append("collector port")
            results['collector_port_previous'] = netflow_config.collectorPort
        if netflow_config.observationDomainId != self.netflow_observation_domain:
            changed = True
            changed_list.append("observation domain ID")
            results['observation_domain_previous'] = netflow_config.observationDomainId
        # looks like switch IP can't be set via SOAP API!?
        if netflow_config.activeFlowTimeout != self.netflow_active_flow_export:
            changed = True
            changed_list.append("active flow export timeout")
            results['active_flow_export_timeout_previous'] = netflow_config.activeFlowTimeout
        if netflow_config.idleFlowTimeout != self.netflow_idle_flow_export:
            changed = True
            changed_list.append("idle flow export timeout")
            results['idle_flow_export_timeout_previous'] = netflow_config.idleFlowTimeout
        if netflow_config.samplingRate != self.netflow_sampling_rate:
            changed = True
            changed_list.append("sampling rate")
            results['sampling_rate_previous'] = netflow_config.samplingRate
        if netflow_config.internalFlowsOnly != self.netflow_process_internal_flows:
            changed = True
            changed_list.append("internal flows")
            results['process_internal_flows_only_previous'] = netflow_config.internalFlowsOnly
        config_spec.ipfixConfig = netflow_config_spec

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
                try:
                    task = self.dvs.ReconfigureDvs_Task(config_spec)
                    wait_for_task(task)
                except TaskError as invalid_argument:
                    self.module.fail_json(
                        msg="Failed to update DVS : %s" % to_native(invalid_argument)
                    )
        else:
            message = "NetFlow already configured properly"
        results['changed'] = changed
        results['result'] = message

        self.module.exit_json(**results)


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            switch=dict(required=True, aliases=['dvswitch']),
            collector_ip=dict(type='str', default=''),
            collector_port=dict(type='int', default=0),
            observation_domain=dict(type='int', default=0),
            # switch_ip=dict(type='str', default=''),
            active_flow_export_timeout=dict(type='int', default=60),
            idle_flow_export_timeout=dict(type='int', default=15),
            sampling_rate=dict(type='int', default=0),
            process_internal_flows_only=dict(type='bool', default=False),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_dvswitch_netflow = VMwareDvSwitchNetFlow(module)
    vmware_dvswitch_netflow.ensure()


if __name__ == '__main__':
    main()

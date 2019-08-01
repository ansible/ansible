#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
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

DOCUMENTATION = r'''
---
module: vmware_cluster_ha
short_description: Manage High Availability (HA) on VMware vSphere clusters
description:
    - Manages HA configuration on VMware vSphere clusters.
    - All values and VMware object names are case sensitive.
version_added: '2.9'
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
requirements:
    - Tested on ESXi 5.5 and 6.5.
    - PyVmomi installed.
options:
    cluster_name:
      description:
      - The name of the cluster to be managed.
      type: str
      required: yes
    datacenter:
      description:
      - The name of the datacenter.
      type: str
      required: yes
      aliases: [ datacenter_name ]
    enable_ha:
      description:
      - Whether to enable HA.
      type: bool
      default: 'no'
    ha_host_monitoring:
      description:
      - Whether HA restarts virtual machines after a host fails.
      - If set to C(enabled), HA restarts virtual machines after a host fails.
      - If set to C(disabled), HA does not restart virtual machines after a host fails.
      - If C(enable_ha) is set to C(no), then this value is ignored.
      type: str
      choices: [ 'enabled', 'disabled' ]
      default: 'enabled'
    ha_vm_monitoring:
      description:
      - State of virtual machine health monitoring service.
      - If set to C(vmAndAppMonitoring), HA response to both virtual machine and application heartbeat failure.
      - If set to C(vmMonitoringDisabled), virtual machine health monitoring is disabled.
      - If set to C(vmMonitoringOnly), HA response to virtual machine heartbeat failure.
      - If C(enable_ha) is set to C(no), then this value is ignored.
      type: str
      choices: ['vmAndAppMonitoring', 'vmMonitoringOnly', 'vmMonitoringDisabled']
      default: 'vmMonitoringDisabled'
    ha_failover_level:
      description:
      - Number of host failures that should be tolerated, still guaranteeing sufficient resources to
        restart virtual machines on available hosts.
      - Accepts integer values only.
      type: int
      default: 2
    ha_admission_control_enabled:
      description:
      - Determines if strict admission control is enabled.
      - It is recommended to set this parameter to C(True), please refer documentation for more details.
      default: True
      type: bool
    ha_vm_failure_interval:
      description:
      - The number of seconds after which virtual machine is declared as failed
        if no heartbeat has been received.
      - This setting is only valid if C(ha_vm_monitoring) is set to, either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - Unit is seconds.
      type: int
      default: 30
    ha_vm_min_up_time:
      description:
      - The number of seconds for the virtual machine's heartbeats to stabilize after
        the virtual machine has been powered on.
      - Valid only when I(ha_vm_monitoring) is set to either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - Unit is seconds.
      type: int
      default: 120
    ha_vm_max_failures:
      description:
      - Maximum number of failures and automated resets allowed during the time
       that C(ha_vm_max_failure_window) specifies.
      - Valid only when I(ha_vm_monitoring) is set to either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      type: int
      default: 3
    ha_vm_max_failure_window:
      description:
      - The number of seconds for the window during which up to C(ha_vm_max_failures) resets
        can occur before automated responses stop.
      - Valid only when I(ha_vm_monitoring) is set to either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - Unit is seconds.
      - Default specifies no failure window.
      type: int
      default: -1
    ha_restart_priority:
      description:
      - Priority HA gives to a virtual machine if sufficient capacity is not available
        to power on all failed virtual machines.
      - Valid only if I(ha_vm_monitoring) is set to either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - If set to C(disabled), then HA is disabled for this virtual machine.
      - If set to C(high), then virtual machine with this priority have a higher chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      - If set to C(medium), then virtual machine with this priority have an intermediate chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      - If set to C(low), then virtual machine with this priority have a lower chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      type: str
      default: 'medium'
      choices: [ 'disabled', 'high', 'low', 'medium' ]
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r"""
- name: Enable HA
  vmware_cluster_ha:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable_ha: yes
  delegate_to: localhost

- name: Enable HA and VM monitoring
  vmware_cluster_ha:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter_name: DC0
    cluster_name: "{{ cluster_name }}"
    enable_ha: True
    ha_vm_monitoring: vmMonitoringOnly
    enable_vsan: True
  delegate_to: localhost
"""

RETURN = r"""#
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, TaskError, find_datacenter_by_name,
                                         vmware_argument_spec, wait_for_task)
from ansible.module_utils._text import to_native


class VMwareCluster(PyVmomi):
    def __init__(self, module):
        super(VMwareCluster, self).__init__(module)
        self.cluster_name = module.params['cluster_name']
        self.datacenter_name = module.params['datacenter']
        self.enable_ha = module.params['enable_ha']
        self.datacenter = None
        self.cluster = None

        self.datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
        if self.datacenter is None:
            self.module.fail_json(msg="Datacenter %s does not exist." % self.datacenter_name)

        self.cluster = self.find_cluster_by_name(cluster_name=self.cluster_name)
        if self.cluster is None:
            self.module.fail_json(msg="Cluster %s does not exist." % self.cluster_name)

    def check_ha_config_diff(self):
        """
        Check HA configuration diff
        Returns: True if there is diff, else False

        """
        das_config = self.cluster.configurationEx.dasConfig
        if das_config.enabled != self.enable_ha or \
                das_config.admissionControlPolicy.failoverLevel != self.params.get('ha_failover_level') or \
                das_config.vmMonitoring != self.params.get('ha_vm_monitoring') or \
                das_config.hostMonitoring != self.params.get('ha_host_monitoring') or \
                das_config.admissionControlPolicy.failoverLevel != self.params.get('ha_failover_level') or \
                das_config.admissionControlEnabled != self.params.get('ha_admission_control_enabled') or \
                das_config.defaultVmSettings.restartPriority != self.params.get('ha_restart_priority') or \
                das_config.defaultVmSettings.vmToolsMonitoringSettings.vmMonitoring != self.params.get('ha_vm_monitoring') or \
                das_config.defaultVmSettings.vmToolsMonitoringSettings.failureInterval != self.params.get('ha_vm_failure_interval') or \
                das_config.defaultVmSettings.vmToolsMonitoringSettings.minUpTime != self.params.get('ha_vm_min_up_time') or \
                das_config.defaultVmSettings.vmToolsMonitoringSettings.maxFailures != self.params.get('ha_vm_max_failures') or \
                das_config.defaultVmSettings.vmToolsMonitoringSettings.maxFailureWindow != self.params.get('ha_vm_max_failure_window'):
            return True
        return False

    def configure_ha(self):
        """
        Manage HA Configuration

        """
        changed, result = False, None

        if self.check_ha_config_diff():
            if not self.module.check_mode:
                cluster_config_spec = vim.cluster.ConfigSpecEx()
                cluster_config_spec.dasConfig = vim.cluster.DasConfigInfo()
                cluster_config_spec.dasConfig.enabled = self.enable_ha
                cluster_config_spec.dasConfig.admissionControlPolicy = vim.cluster.FailoverLevelAdmissionControlPolicy()
                cluster_config_spec.dasConfig.admissionControlPolicy.failoverLevel = self.params.get('ha_failover_level')

                ha_vm_monitoring = self.params.get('ha_vm_monitoring')
                das_vm_config = None
                if ha_vm_monitoring in ['vmMonitoringOnly', 'vmAndAppMonitoring']:
                    vm_tool_spec = vim.cluster.VmToolsMonitoringSettings()
                    vm_tool_spec.enabled = True
                    vm_tool_spec.vmMonitoring = ha_vm_monitoring
                    vm_tool_spec.failureInterval = self.params.get('ha_vm_failure_interval')
                    vm_tool_spec.minUpTime = self.params.get('ha_vm_min_up_time')
                    vm_tool_spec.maxFailures = self.params.get('ha_vm_max_failures')
                    vm_tool_spec.maxFailureWindow = self.params.get('ha_vm_max_failure_window')

                    das_vm_config = vim.cluster.DasVmSettings()
                    das_vm_config.restartPriority = self.params.get('ha_restart_priority')
                    das_vm_config.isolationResponse = None
                    das_vm_config.vmToolsMonitoringSettings = vm_tool_spec

                cluster_config_spec.dasConfig.admissionControlEnabled = self.params.get('ha_admission_control_enabled')

                cluster_config_spec.dasConfig.hostMonitoring = self.params.get('ha_host_monitoring')
                cluster_config_spec.dasConfig.vmMonitoring = ha_vm_monitoring
                cluster_config_spec.dasConfig.defaultVmSettings = das_vm_config
                try:
                    task = self.cluster.ReconfigureComputeResource_Task(cluster_config_spec, True)
                    changed, result = wait_for_task(task)
                except vmodl.RuntimeFault as runtime_fault:
                    self.module.fail_json(msg=to_native(runtime_fault.msg))
                except vmodl.MethodFault as method_fault:
                    self.module.fail_json(msg=to_native(method_fault.msg))
                except TaskError as task_e:
                    self.module.fail_json(msg=to_native(task_e))
                except Exception as generic_exc:
                    self.module.fail_json(msg="Failed to update cluster"
                                              " due to generic exception %s" % to_native(generic_exc))
            else:
                changed = True

        self.module.exit_json(changed=changed, result=result)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        datacenter=dict(type='str', required=True, aliases=['datacenter_name']),
        # HA
        enable_ha=dict(type='bool', default=False),
        ha_failover_level=dict(type='int', default=2),
        ha_host_monitoring=dict(type='str',
                                default='enabled',
                                choices=['enabled', 'disabled']),
        # HA VM Monitoring related parameters
        ha_vm_monitoring=dict(type='str',
                              choices=['vmAndAppMonitoring', 'vmMonitoringOnly', 'vmMonitoringDisabled'],
                              default='vmMonitoringDisabled'),
        ha_vm_failure_interval=dict(type='int', default=30),
        ha_vm_min_up_time=dict(type='int', default=120),
        ha_vm_max_failures=dict(type='int', default=3),
        ha_vm_max_failure_window=dict(type='int', default=-1),

        ha_restart_priority=dict(type='str',
                                 choices=['high', 'low', 'medium', 'disabled'],
                                 default='medium'),
        ha_admission_control_enabled=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_cluster_ha = VMwareCluster(module)
    vmware_cluster_ha.configure_ha()


if __name__ == '__main__':
    main()

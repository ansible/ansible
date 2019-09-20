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
    host_isolation_response:
      description:
      - Indicates whether or VMs should be powered off if a host determines that it is isolated from the rest of the compute resource.
      - If set to C(none), do not power off VMs in the event of a host network isolation.
      - If set to C(powerOff), power off VMs in the event of a host network isolation.
      - If set to C(shutdown), shut down VMs guest operating system in the event of a host network isolation.
      type: str
      choices: ['none', 'powerOff', 'shutdown']
      default: 'none'
    slot_based_admission_control:
      description:
      - Configure slot based admission control policy.
      - C(slot_based_admission_control), C(reservation_based_admission_control) and C(failover_host_admission_control) are mutually exclusive.
      suboptions:
        failover_level:
          description:
            - Number of host failures that should be tolerated.
          type: int
          required: true
      type: dict
    reservation_based_admission_control:
      description:
      - Configure reservation based admission control policy.
      - C(slot_based_admission_control), C(reservation_based_admission_control) and C(failover_host_admission_control) are mutually exclusive.
      suboptions:
        failover_level:
          description:
            - Number of host failures that should be tolerated.
          type: int
          required: true
        auto_compute_percentages:
          description:
            - By default, C(failover_level) is used to calculate C(cpu_failover_resources_percent) and C(memory_failover_resources_percent).
              If a user wants to override the percentage values, he has to set this field to false.
          type: bool
          default: true
        cpu_failover_resources_percent:
          description:
          - Percentage of CPU resources in the cluster to reserve for failover.
            Ignored if C(auto_compute_percentages) is not set to false.
          type: int
          default: 50
        memory_failover_resources_percent:
          description:
          - Percentage of memory resources in the cluster to reserve for failover.
            Ignored if C(auto_compute_percentages) is not set to false.
          type: int
          default: 50
      type: dict
    failover_host_admission_control:
      description:
      - Configure dedicated failover hosts.
      - C(slot_based_admission_control), C(reservation_based_admission_control) and C(failover_host_admission_control) are mutually exclusive.
      suboptions:
        failover_hosts:
          description:
            - List of dedicated failover hosts.
          type: list
          required: true
      type: dict
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
- name: Enable HA without admission control
  vmware_cluster_ha:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable_ha: yes
  delegate_to: localhost

- name: Enable HA and VM monitoring without admission control
  vmware_cluster_ha:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter_name: DC0
    cluster_name: "{{ cluster_name }}"
    enable_ha: True
    ha_vm_monitoring: vmMonitoringOnly
  delegate_to: localhost

- name: Enable HA with admission control reserving 50% of resources for HA
  vmware_cluster_ha:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable_ha: yes
    reservation_based_admission_control:
      auto_compute_percentages: False
      failover_level: 1
      cpu_failover_resources_percent: 50
      memory_failover_resources_percent: 50
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
        self.host_isolation_response = getattr(vim.cluster.DasVmSettings.IsolationResponse, self.params.get('host_isolation_response'))

        if self.enable_ha and (
                self.params.get('slot_based_admission_control') or
                self.params.get('reservation_based_admission_control') or
                self.params.get('failover_host_admission_control')):
            self.ha_admission_control = True
        else:
            self.ha_admission_control = False

        self.datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
        if self.datacenter is None:
            self.module.fail_json(msg="Datacenter %s does not exist." % self.datacenter_name)

        self.cluster = self.find_cluster_by_name(cluster_name=self.cluster_name)
        if self.cluster is None:
            self.module.fail_json(msg="Cluster %s does not exist." % self.cluster_name)

    def get_failover_hosts(self):
        """
        Get failover hosts for failover_host_admission_control policy
        Returns: List of ESXi hosts sorted by name

        """
        policy = self.params.get('failover_host_admission_control')
        hosts = []
        all_hosts = dict((h.name, h) for h in self.get_all_hosts_by_cluster(self.cluster_name))
        for host in policy.get('failover_hosts'):
            if host in all_hosts:
                hosts.append(all_hosts.get(host))
            else:
                self.module.fail_json(msg="Host %s is not a member of cluster %s." % (host, self.cluster_name))
        hosts.sort(key=lambda h: h.name)
        return hosts

    def check_ha_config_diff(self):
        """
        Check HA configuration diff
        Returns: True if there is diff, else False

        """
        das_config = self.cluster.configurationEx.dasConfig
        if das_config.enabled != self.enable_ha:
            return True

        if self.enable_ha and (
                das_config.vmMonitoring != self.params.get('ha_vm_monitoring') or
                das_config.hostMonitoring != self.params.get('ha_host_monitoring') or
                das_config.admissionControlEnabled != self.ha_admission_control or
                das_config.defaultVmSettings.restartPriority != self.params.get('ha_restart_priority') or
                das_config.defaultVmSettings.isolationResponse != self.host_isolation_response or
                das_config.defaultVmSettings.vmToolsMonitoringSettings.vmMonitoring != self.params.get('ha_vm_monitoring') or
                das_config.defaultVmSettings.vmToolsMonitoringSettings.failureInterval != self.params.get('ha_vm_failure_interval') or
                das_config.defaultVmSettings.vmToolsMonitoringSettings.minUpTime != self.params.get('ha_vm_min_up_time') or
                das_config.defaultVmSettings.vmToolsMonitoringSettings.maxFailures != self.params.get('ha_vm_max_failures') or
                das_config.defaultVmSettings.vmToolsMonitoringSettings.maxFailureWindow != self.params.get('ha_vm_max_failure_window')):
            return True

        if self.ha_admission_control:
            if self.params.get('slot_based_admission_control'):
                policy = self.params.get('slot_based_admission_control')
                if not isinstance(das_config.admissionControlPolicy, vim.cluster.FailoverLevelAdmissionControlPolicy) or \
                        das_config.admissionControlPolicy.failoverLevel != policy.get('failover_level'):
                    return True
            elif self.params.get('reservation_based_admission_control'):
                policy = self.params.get('reservation_based_admission_control')
                auto_compute_percentages = policy.get('auto_compute_percentages')
                if not isinstance(das_config.admissionControlPolicy, vim.cluster.FailoverResourcesAdmissionControlPolicy) or \
                        das_config.admissionControlPolicy.autoComputePercentages != auto_compute_percentages or \
                        das_config.admissionControlPolicy.failoverLevel != policy.get('failover_level'):
                    return True
                if not auto_compute_percentages:
                    if das_config.admissionControlPolicy.cpuFailoverResourcesPercent != policy.get('cpu_failover_resources_percent') or \
                            das_config.admissionControlPolicy.memoryFailoverResourcesPercent != policy.get('memory_failover_resources_percent'):
                        return True
            elif self.params.get('failover_host_admission_control'):
                policy = self.params.get('failover_host_admission_control')
                if not isinstance(das_config.admissionControlPolicy, vim.cluster.FailoverHostAdmissionControlPolicy):
                    return True
                das_config.admissionControlPolicy.failoverHosts.sort(key=lambda h: h.name)
                if das_config.admissionControlPolicy.failoverHosts != self.get_failover_hosts():
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

                if self.enable_ha:
                    vm_tool_spec = vim.cluster.VmToolsMonitoringSettings()
                    vm_tool_spec.enabled = True
                    vm_tool_spec.vmMonitoring = self.params.get('ha_vm_monitoring')
                    vm_tool_spec.failureInterval = self.params.get('ha_vm_failure_interval')
                    vm_tool_spec.minUpTime = self.params.get('ha_vm_min_up_time')
                    vm_tool_spec.maxFailures = self.params.get('ha_vm_max_failures')
                    vm_tool_spec.maxFailureWindow = self.params.get('ha_vm_max_failure_window')

                    das_vm_config = vim.cluster.DasVmSettings()
                    das_vm_config.restartPriority = self.params.get('ha_restart_priority')
                    das_vm_config.isolationResponse = self.host_isolation_response
                    das_vm_config.vmToolsMonitoringSettings = vm_tool_spec
                    cluster_config_spec.dasConfig.defaultVmSettings = das_vm_config

                cluster_config_spec.dasConfig.admissionControlEnabled = self.ha_admission_control

                if self.ha_admission_control:
                    if self.params.get('slot_based_admission_control'):
                        cluster_config_spec.dasConfig.admissionControlPolicy = vim.cluster.FailoverLevelAdmissionControlPolicy()
                        policy = self.params.get('slot_based_admission_control')
                        cluster_config_spec.dasConfig.admissionControlPolicy.failoverLevel = policy.get('failover_level')
                    elif self.params.get('reservation_based_admission_control'):
                        cluster_config_spec.dasConfig.admissionControlPolicy = vim.cluster.FailoverResourcesAdmissionControlPolicy()
                        policy = self.params.get('reservation_based_admission_control')
                        auto_compute_percentages = policy.get('auto_compute_percentages')
                        cluster_config_spec.dasConfig.admissionControlPolicy.autoComputePercentages = auto_compute_percentages
                        cluster_config_spec.dasConfig.admissionControlPolicy.failoverLevel = policy.get('failover_level')
                        if not auto_compute_percentages:
                            cluster_config_spec.dasConfig.admissionControlPolicy.cpuFailoverResourcesPercent = \
                                policy.get('cpu_failover_resources_percent')
                            cluster_config_spec.dasConfig.admissionControlPolicy.memoryFailoverResourcesPercent = \
                                policy.get('memory_failover_resources_percent')
                    elif self.params.get('failover_host_admission_control'):
                        cluster_config_spec.dasConfig.admissionControlPolicy = vim.cluster.FailoverHostAdmissionControlPolicy()
                        policy = self.params.get('failover_host_admission_control')
                        cluster_config_spec.dasConfig.admissionControlPolicy.failoverHosts = self.get_failover_hosts()

                cluster_config_spec.dasConfig.hostMonitoring = self.params.get('ha_host_monitoring')
                cluster_config_spec.dasConfig.vmMonitoring = self.params.get('ha_vm_monitoring')

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
        ha_host_monitoring=dict(type='str',
                                default='enabled',
                                choices=['enabled', 'disabled']),
        host_isolation_response=dict(type='str',
                                     default='none',
                                     choices=['none', 'powerOff', 'shutdown']),
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
        # HA Admission Control related parameters
        slot_based_admission_control=dict(type='dict', options=dict(
            failover_level=dict(type='int', required=True),
        )),
        reservation_based_admission_control=dict(type='dict', options=dict(
            auto_compute_percentages=dict(type='bool', default=True),
            failover_level=dict(type='int', required=True),
            cpu_failover_resources_percent=dict(type='int', default=50),
            memory_failover_resources_percent=dict(type='int', default=50),
        )),
        failover_host_admission_control=dict(type='dict', options=dict(
            failover_hosts=dict(type='list', elements='str', required=True),
        )),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['slot_based_admission_control', 'reservation_based_admission_control', 'failover_host_admission_control']
        ]
    )

    vmware_cluster_ha = VMwareCluster(module)
    vmware_cluster_ha.configure_ha()


if __name__ == '__main__':
    main()

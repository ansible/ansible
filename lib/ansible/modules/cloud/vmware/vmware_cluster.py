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
module: vmware_cluster
short_description: Manage VMware vSphere clusters
description:
    - Adds or removes VMware vSphere clusters.
    - Although this module can manage DRS, HA and VSAN related configurations, this functionality is deprecated and will be removed in 2.12.
    - To manage DRS, HA and VSAN related configurations, use the new modules vmware_cluster_drs, vmware_cluster_ha and vmware_cluster_vsan.
    - All values and VMware object names are case sensitive.
version_added: '2.0'
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
    ignore_drs:
      description:
      - If set to C(yes), DRS will not be configured; all explicit and default DRS related configurations will be ignored.
      type: bool
      default: 'no'
      version_added: 2.9
    ignore_ha:
      description:
      - If set to C(yes), HA will not be configured; all explicit and default HA related configurations will be ignored.
      type: bool
      default: 'no'
      version_added: 2.9
    ignore_vsan:
      description:
      - If set to C(yes), VSAN will not be configured; all explicit and default VSAN related configurations will be ignored.
      type: bool
      default: 'no'
      version_added: 2.9
    enable_drs:
      description:
      - If set to C(yes), will enable DRS when the cluster is created.
      - Use C(enable_drs) of M(vmware_cluster_drs) instead.
      - Deprecated option, will be removed in version 2.12.
      type: bool
      default: 'no'
    drs_enable_vm_behavior_overrides:
      description:
      - Determines whether DRS Behavior overrides for individual virtual machines are enabled.
      - If set to C(True), overrides C(drs_default_vm_behavior).
      - Use C(drs_enable_vm_behavior_overrides) of M(vmware_cluster_drs) instead.
      - Deprecated option, will be removed in version 2.12.
      type: bool
      default: True
      version_added: 2.8
    drs_default_vm_behavior:
      description:
      - Specifies the cluster-wide default DRS behavior for virtual machines.
      - If set to C(partiallyAutomated), then vCenter generate recommendations for virtual machine migration and
        for the placement with a host. vCenter automatically implement placement at power on.
      - If set to C(manual), then vCenter generate recommendations for virtual machine migration and
        for the placement with a host. vCenter should not implement the recommendations automatically.
      - If set to C(fullyAutomated), then vCenter should automate both the migration of virtual machines
        and their placement with a host at power on.
      - Use C(drs_default_vm_behavior) of M(vmware_cluster_drs) instead.
      - Deprecated option, will be removed in version 2.12.
      default: fullyAutomated
      choices: [ fullyAutomated, manual, partiallyAutomated ]
      version_added: 2.8
    drs_vmotion_rate:
      description:
      - Threshold for generated ClusterRecommendations.
      - Use C(drs_vmotion_rate) of M(vmware_cluster_drs) instead.
      - Deprecated option, will be removed in version 2.12.
      default: 3
      choices: [ 1, 2, 3, 4, 5 ]
      version_added: 2.8
    enable_ha:
      description:
      - If set to C(yes) will enable HA when the cluster is created.
      - Use C(enable_ha) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      type: bool
      default: 'no'
    ha_host_monitoring:
      description:
      - Indicates whether HA restarts virtual machines after a host fails.
      - If set to C(enabled), HA restarts virtual machines after a host fails.
      - If set to C(disabled), HA does not restart virtual machines after a host fails.
      - If C(enable_ha) is set to C(no), then this value is ignored.
      - Use C(ha_host_monitoring) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      choices: [ 'enabled', 'disabled' ]
      default: 'enabled'
      version_added: 2.8
    ha_vm_monitoring:
      description:
      - Indicates the state of virtual machine health monitoring service.
      - If set to C(vmAndAppMonitoring), HA response to both virtual machine and application heartbeat failure.
      - If set to C(vmMonitoringDisabled), virtual machine health monitoring is disabled.
      - If set to C(vmMonitoringOnly), HA response to virtual machine heartbeat failure.
      - If C(enable_ha) is set to C(no), then this value is ignored.
      - Use C(ha_vm_monitoring) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      choices: ['vmAndAppMonitoring', 'vmMonitoringOnly', 'vmMonitoringDisabled']
      default: 'vmMonitoringDisabled'
      version_added: 2.8
    ha_failover_level:
      description:
      - Number of host failures that should be tolerated, still guaranteeing sufficient resources to
        restart virtual machines on available hosts.
      - Accepts integer values only.
      - Use C(slot_based_admission_control), C(reservation_based_admission_control) or C(failover_host_admission_control) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      default: 2
      version_added: 2.8
    ha_admission_control_enabled:
      description:
      - Determines if strict admission control is enabled.
      - It is recommended to set this parameter to C(True), please refer documentation for more details.
      - Use C(slot_based_admission_control), C(reservation_based_admission_control) or C(failover_host_admission_control) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      default: True
      type: bool
      version_added: 2.8
    ha_vm_failure_interval:
      description:
      - The number of seconds after which virtual machine is declared as failed
        if no heartbeat has been received.
      - This setting is only valid if C(ha_vm_monitoring) is set to, either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - Unit is seconds.
      - Use C(ha_vm_failure_interval) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      default: 30
      version_added: 2.8
    ha_vm_min_up_time:
      description:
      - The number of seconds for the virtual machine's heartbeats to stabilize after
        the virtual machine has been powered on.
      - This setting is only valid if C(ha_vm_monitoring) is set to, either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - Unit is seconds.
      - Use C(ha_vm_min_up_time) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      default: 120
      version_added: 2.8
    ha_vm_max_failures:
      description:
      - Maximum number of failures and automated resets allowed during the time
       that C(ha_vm_max_failure_window) specifies.
      - This setting is only valid if C(ha_vm_monitoring) is set to, either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - Use C(ha_vm_max_failures) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      default: 3
      version_added: 2.8
    ha_vm_max_failure_window:
      description:
      - The number of seconds for the window during which up to C(ha_vm_max_failures) resets
        can occur before automated responses stop.
      - This setting is only valid if C(ha_vm_monitoring) is set to, either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - Unit is seconds.
      - Default specifies no failure window.
      - Use C(ha_vm_max_failure_window) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      default: -1
      version_added: 2.8
    ha_restart_priority:
      description:
      - Determines the preference that HA gives to a virtual machine if sufficient capacity is not available
        to power on all failed virtual machines.
      - This setting is only valid if C(ha_vm_monitoring) is set to, either C(vmAndAppMonitoring) or C(vmMonitoringOnly).
      - If set to C(disabled), then HA is disabled for this virtual machine.
      - If set to C(high), then virtual machine with this priority have a higher chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      - If set to C(medium), then virtual machine with this priority have an intermediate chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      - If set to C(low), then virtual machine with this priority have a lower chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      - Use C(ha_restart_priority) of M(vmware_cluster_ha) instead.
      - Deprecated option, will be removed in version 2.12.
      default: 'medium'
      version_added: 2.8
      choices: [ 'disabled', 'high', 'low', 'medium' ]
    enable_vsan:
      description:
      - If set to C(yes) will enable vSAN when the cluster is created.
      - Use C(enable_vsan) of M(vmware_cluster_vsan) instead.
      - Deprecated option, will be removed in version 2.12.
      type: bool
      default: 'no'
    vsan_auto_claim_storage:
      description:
      - Determines whether the VSAN service is configured to automatically claim local storage
        on VSAN-enabled hosts in the cluster.
      - Use C(vsan_auto_claim_storage) of M(vmware_cluster_vsan) instead.
      - Deprecated option, will be removed in version 2.12.
      type: bool
      default: False
      version_added: 2.8
    state:
      description:
      - Create C(present) or remove C(absent) a VMware vSphere cluster.
      choices: [ absent, present ]
      default: present
seealso:
- module: vmware_cluster_drs
- module: vmware_cluster_ha
- module: vmware_cluster_vsan
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r"""
- name: Create Cluster
  vmware_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable_ha: yes
    enable_drs: yes
    enable_vsan: yes
  delegate_to: localhost

- name: Create Cluster with additional changes
  vmware_cluster:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    validate_certs: no
    datacenter_name: DC0
    cluster_name: "{{ cluster_name }}"
    enable_ha: True
    ha_vm_monitoring: vmMonitoringOnly
    enable_drs: True
    drs_default_vm_behavior: partiallyAutomated
    enable_vsan: True
  register: cl_result
  delegate_to: localhost

- name: Delete Cluster
  vmware_cluster:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    datacenter_name: datacenter
    cluster_name: cluster
    enable_ha: yes
    enable_drs: yes
    enable_vsan: yes
    state: absent
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
        self.ignore_drs = module.params['ignore_drs']
        self.ignore_ha = module.params['ignore_ha']
        self.ignore_vsan = module.params['ignore_vsan']
        self.enable_drs = module.params['enable_drs']
        self.enable_ha = module.params['enable_ha']
        self.enable_vsan = module.params['enable_vsan']
        self.desired_state = module.params['state']
        self.datacenter = None
        self.cluster = None

    def process_state(self):
        """
        Manage internal states of cluster
        """
        cluster_states = {
            'absent': {
                'present': self.state_destroy_cluster,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_update_cluster,
                'absent': self.state_create_cluster,
            }
        }
        current_state = self.check_cluster_configuration()
        # Based on the desired_state and the current_state call
        # the appropriate method from the dictionary
        cluster_states[self.desired_state][current_state]()

    def configure_ha(self):
        """
        Manage HA Configuration
        Returns: Cluster DAS configuration spec

        """
        msg = 'Configuring HA using vmware_cluster module is deprecated and will be removed in version 2.12. ' \
              'Please use vmware_cluster_ha module for the new functionality.'
        self.module.deprecate(msg, '2.12')

        das_config = vim.cluster.DasConfigInfo()
        das_config.enabled = self.enable_ha
        das_config.admissionControlPolicy = vim.cluster.FailoverLevelAdmissionControlPolicy()
        das_config.admissionControlPolicy.failoverLevel = self.params.get('ha_failover_level')

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

        das_config.admissionControlEnabled = self.params.get('ha_admission_control_enabled')

        das_config.hostMonitoring = self.params.get('ha_host_monitoring')
        das_config.vmMonitoring = ha_vm_monitoring
        das_config.defaultVmSettings = das_vm_config

        return das_config

    def configure_drs(self):
        """
        Manage DRS configuration
        Returns: Cluster DRS configuration spec

        """
        msg = 'Configuring DRS using vmware_cluster module is deprecated and will be removed in version 2.12. ' \
              'Please use vmware_cluster_drs module for the new functionality.'
        self.module.deprecate(msg, '2.12')

        drs_config = vim.cluster.DrsConfigInfo()

        drs_config.enabled = self.enable_drs
        drs_config.enableVmBehaviorOverrides = self.params.get('drs_enable_vm_behavior_overrides')
        drs_config.defaultVmBehavior = self.params.get('drs_default_vm_behavior')
        drs_config.vmotionRate = self.params.get('drs_vmotion_rate')

        return drs_config

    def configure_vsan(self):
        """
        Manage VSAN configuration
        Returns: Cluster VSAN configuration spec

        """
        msg = 'Configuring VSAN using vmware_cluster module is deprecated and will be removed in version 2.12. ' \
              'Please use vmware_cluster_vsan module for the new functionality.'
        self.module.deprecate(msg, '2.12')

        vsan_config = vim.vsan.cluster.ConfigInfo()
        vsan_config.enabled = self.enable_vsan
        vsan_config.defaultConfig = vim.vsan.cluster.ConfigInfo.HostDefaultInfo()
        vsan_config.defaultConfig.autoClaimStorage = self.params.get('vsan_auto_claim_storage')
        return vsan_config

    def state_create_cluster(self):
        """
        Create cluster with given configuration
        """
        try:
            cluster_config_spec = vim.cluster.ConfigSpecEx()
            if not self.ignore_ha:
                cluster_config_spec.dasConfig = self.configure_ha()
            if not self.ignore_drs:
                cluster_config_spec.drsConfig = self.configure_drs()
            if self.enable_vsan and not self.ignore_vsan:
                cluster_config_spec.vsanConfig = self.configure_vsan()
            if not self.module.check_mode:
                self.datacenter.hostFolder.CreateClusterEx(self.cluster_name, cluster_config_spec)
            self.module.exit_json(changed=True)
        except vim.fault.DuplicateName:
            # To match other vmware_* modules
            pass
        except vmodl.fault.InvalidArgument as invalid_args:
            self.module.fail_json(msg="Cluster configuration specification"
                                      " parameter is invalid : %s" % to_native(invalid_args.msg))
        except vim.fault.InvalidName as invalid_name:
            self.module.fail_json(msg="'%s' is an invalid name for a"
                                      " cluster : %s" % (self.cluster_name,
                                                         to_native(invalid_name.msg)))
        except vmodl.fault.NotSupported as not_supported:
            # This should never happen
            self.module.fail_json(msg="Trying to create a cluster on an incorrect"
                                      " folder object : %s" % to_native(not_supported.msg))
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            # This should never happen either
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to create cluster"
                                      " due to generic exception %s" % to_native(generic_exc))

    def state_destroy_cluster(self):
        """
        Destroy cluster
        """
        changed, result = True, None

        try:
            if not self.module.check_mode:
                task = self.cluster.Destroy_Task()
                changed, result = wait_for_task(task)
            self.module.exit_json(changed=changed, result=result)
        except vim.fault.VimFault as vim_fault:
            self.module.fail_json(msg=to_native(vim_fault.msg))
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to destroy cluster"
                                      " due to generic exception %s" % to_native(generic_exc))

    def state_exit_unchanged(self):
        """
        Exit without any change
        """
        self.module.exit_json(changed=False)

    def state_update_cluster(self):
        """
        Update cluster configuration of existing cluster
        """
        changed, result = False, None
        cluster_config_spec = vim.cluster.ConfigSpecEx()
        diff = False  # Triggers Reconfigure Task only when there is a change
        if self.check_ha_config_diff() and not self.ignore_ha:
            cluster_config_spec.dasConfig = self.configure_ha()
            diff = True
        if self.check_drs_config_diff() and not self.ignore_drs:
            cluster_config_spec.drsConfig = self.configure_drs()
            diff = True
        if self.check_vsan_config_diff() and not self.ignore_vsan:
            cluster_config_spec.vsanConfig = self.configure_vsan()
            diff = True

        try:
            if not self.module.check_mode and diff:
                task = self.cluster.ReconfigureComputeResource_Task(cluster_config_spec, True)
                changed, result = wait_for_task(task)
            self.module.exit_json(changed=changed, result=result)
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except TaskError as task_e:
            self.module.fail_json(msg=to_native(task_e))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to update cluster"
                                      " due to generic exception %s" % to_native(generic_exc))

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

    def check_drs_config_diff(self):
        """
        Check DRS configuration diff
        Returns: True if there is diff, else False

        """
        drs_config = self.cluster.configurationEx.drsConfig

        if drs_config.enabled != self.enable_drs or \
                drs_config.enableVmBehaviorOverrides != self.params.get('drs_enable_vm_behavior_overrides') or \
                drs_config.defaultVmBehavior != self.params.get('drs_default_vm_behavior') or \
                drs_config.vmotionRate != self.params.get('drs_vmotion_rate'):
            return True
        return False

    def check_vsan_config_diff(self):
        """
        Check VSAN configuration diff
        Returns: True if there is diff, else False

        """
        vsan_config = self.cluster.configurationEx.vsanConfigInfo

        if vsan_config.enabled != self.enable_vsan or \
                vsan_config.defaultConfig.autoClaimStorage != self.params.get('vsan_auto_claim_storage'):
            return True
        return False

    def check_cluster_configuration(self):
        """
        Check cluster configuration
        Returns: 'Present' if cluster exists, else 'absent'

        """
        try:
            self.datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
            if self.datacenter is None:
                self.module.fail_json(msg="Datacenter %s does not exist." % self.datacenter_name)
            self.cluster = self.find_cluster_by_name(cluster_name=self.cluster_name)

            if self.cluster is None:
                return 'absent'

            return 'present'
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to check configuration"
                                      " due to generic exception %s" % to_native(generic_exc))


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        datacenter=dict(type='str', required=True, aliases=['datacenter_name']),
        state=dict(type='str',
                   default='present',
                   choices=['absent', 'present']),
        # DRS
        ignore_drs=dict(type='bool', default=False),
        enable_drs=dict(type='bool', default=False),
        drs_enable_vm_behavior_overrides=dict(type='bool', default=True),
        drs_default_vm_behavior=dict(type='str',
                                     choices=['fullyAutomated', 'manual', 'partiallyAutomated'],
                                     default='fullyAutomated'),
        drs_vmotion_rate=dict(type='int',
                              choices=range(1, 6),
                              default=3),
        # HA
        ignore_ha=dict(type='bool', default=False),
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
        # VSAN
        ignore_vsan=dict(type='bool', default=False),
        enable_vsan=dict(type='bool', default=False),
        vsan_auto_claim_storage=dict(type='bool', default=False),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_cluster = VMwareCluster(module)
    vmware_cluster.process_state()


if __name__ == '__main__':
    main()

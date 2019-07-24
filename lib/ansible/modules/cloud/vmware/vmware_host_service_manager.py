#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_host_service_manager
short_description: Manage services on a given ESXi host
description:
- This module can be used to manage (start, stop, restart) services on a given ESXi host.
- If cluster_name is provided, specified service will be managed on all ESXi host belonging to that cluster.
- If specific esxi_hostname is provided, then specified service will be managed on given ESXi host only.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of the cluster.
    - Service settings are applied to every ESXi host system/s in given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
    type: str
  esxi_hostname:
    description:
    - ESXi hostname.
    - Service settings are applied to this ESXi host system.
    - If C(cluster_name) is not given, this parameter is required.
    type: str
  state:
    description:
    - Desired state of service.
    - "State value 'start' and 'present' has same effect."
    - "State value 'stop' and 'absent' has same effect."
    choices: [ absent, present, restart, start, stop ]
    type: str
    default: 'start'
  service_policy:
    description:
    - Set of valid service policy strings.
    - If set C(on), then service should be started when the host starts up.
    - If set C(automatic), then service should run if and only if it has open firewall ports.
    - If set C(off), then Service should not be started when the host starts up.
    choices: [ 'automatic', 'off', 'on' ]
    type: str
  service_name:
    description:
    - Name of Service to be managed. This is a brief identifier for the service, for example, ntpd, vxsyslogd etc.
    - This value should be a valid ESXi service name.
    required: True
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Start ntpd service setting for all ESXi Host in given Cluster
  vmware_host_service_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
    service_name: ntpd
    state: present
  delegate_to: localhost

- name: Start ntpd setting for an ESXi Host
  vmware_host_service_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    service_name: ntpd
    state: present
  delegate_to: localhost

- name: Start ntpd setting for an ESXi Host with Service policy
  vmware_host_service_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    service_name: ntpd
    service_policy: on
    state: present
  delegate_to: localhost

- name: Stop ntpd setting for an ESXi Host
  vmware_host_service_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    service_name: ntpd
    state: absent
  delegate_to: localhost
'''

RETURN = r'''#
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


class VmwareServiceManager(PyVmomi):
    def __init__(self, module):
        super(VmwareServiceManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.options = self.params.get('options', dict())
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        self.desired_state = self.params.get('state')
        self.desired_policy = self.params.get('service_policy', None)
        self.service_name = self.params.get('service_name')
        self.results = {}

    def service_ctrl(self):
        changed = False
        host_service_state = []
        for host in self.hosts:
            actual_service_state, actual_service_policy = self.check_service_state(host=host, service_name=self.service_name)
            host_service_system = host.configManager.serviceSystem
            if host_service_system:
                changed_state = False
                self.results[host.name] = dict(service_name=self.service_name,
                                               actual_service_state='running' if actual_service_state else 'stopped',
                                               actual_service_policy=actual_service_policy,
                                               desired_service_policy=self.desired_policy,
                                               desired_service_state=self.desired_state,
                                               error='',
                                               )
                try:
                    if self.desired_state in ['start', 'present']:
                        if not actual_service_state:
                            if not self.module.check_mode:
                                host_service_system.StartService(id=self.service_name)
                            changed_state = True
                    elif self.desired_state in ['stop', 'absent']:
                        if actual_service_state:
                            if not self.module.check_mode:
                                host_service_system.StopService(id=self.service_name)
                            changed_state = True
                    elif self.desired_state == 'restart':
                        if not self.module.check_mode:
                            host_service_system.RestartService(id=self.service_name)
                        changed_state = True

                    if self.desired_policy:
                        if actual_service_policy != self.desired_policy:
                            if not self.module.check_mode:
                                host_service_system.UpdateServicePolicy(id=self.service_name,
                                                                        policy=self.desired_policy)
                            changed_state = True

                    host_service_state.append(changed_state)
                    self.results[host.name].update(changed=changed_state)
                except (vim.fault.InvalidState, vim.fault.NotFound,
                        vim.fault.HostConfigFault, vmodl.fault.InvalidArgument) as e:
                    self.results[host.name].update(changed=False,
                                                   error=to_native(e.msg))

        if any(host_service_state):
            changed = True
        self.module.exit_json(changed=changed, results=self.results)

    def check_service_state(self, host, service_name):
        host_service_system = host.configManager.serviceSystem
        if host_service_system:
            services = host_service_system.serviceInfo.service
            for service in services:
                if service.key == service_name:
                    return service.running, service.policy

        msg = "Failed to find '%s' service on host system '%s'" % (service_name, host.name)
        cluster_name = self.params.get('cluster_name', None)
        if cluster_name:
            msg += " located on cluster '%s'" % cluster_name
        msg += ", please check if you have specified a valid ESXi service name."
        self.module.fail_json(msg=msg)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        state=dict(type='str', default='start', choices=['absent', 'present', 'restart', 'start', 'stop']),
        service_name=dict(type='str', required=True),
        service_policy=dict(type='str', choices=['automatic', 'off', 'on']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        supports_check_mode=True
    )

    vmware_host_service = VmwareServiceManager(module)
    vmware_host_service.service_ctrl()


if __name__ == "__main__":
    main()

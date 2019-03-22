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
module: vmware_host_acceptance
short_description: Manage the host acceptance level of an ESXi host
description:
- This module can be used to manage the host acceptance level of an ESXi host.
- The host acceptance level controls the acceptance level of each VIB on a ESXi host.
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
    - Acceptance level of all ESXi host system in the given cluster will be managed.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname.
    - Acceptance level of this ESXi host system will be managed.
    - If C(cluster_name) is not given, this parameter is required.
  state:
    description:
    - Set or list acceptance level of the given ESXi host.
    - 'If set to C(list), then will return current acceptance level of given host system/s.'
    - If set to C(present), then will set given acceptance level.
    choices: [ list, present ]
    required: False
    default: 'list'
  acceptance_level:
    description:
    - Name of acceptance level.
    - If set to C(partner), then accept only partner and VMware signed and certified VIBs.
    - If set to C(vmware_certified), then accept only VIBs that are signed and certified by VMware.
    - If set to C(vmware_accepted), then accept VIBs that have been accepted by VMware.
    - If set to C(community), then accept all VIBs, even those that are not signed.
    choices: [ community, partner, vmware_accepted, vmware_certified ]
    required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Set acceptance level to community for all ESXi Host in given Cluster
  vmware_host_acceptance:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
    acceptance_level: 'community'
    state: present
  delegate_to: localhost
  register: cluster_acceptance_level

- name: Set acceptance level to vmware_accepted for the given ESXi Host
  vmware_host_acceptance:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    acceptance_level: 'vmware_accepted'
    state: present
  delegate_to: localhost
  register: host_acceptance_level

- name: Get acceptance level from the given ESXi Host
  vmware_host_acceptance:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: list
  delegate_to: localhost
  register: host_acceptance_level
'''

RETURN = r'''
facts:
    description:
    - dict with hostname as key and dict with acceptance level facts, error as value
    returned: facts
    type: dict
    sample: { "facts": { "localhost.localdomain": { "error": "NA", "level": "vmware_certified" }}}
'''

try:
    from pyVmomi import vim
except ImportError:
    pass
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


class VMwareAccpetanceManager(PyVmomi):
    def __init__(self, module):
        super(VMwareAccpetanceManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        self.desired_state = self.params.get('state')
        self.hosts_facts = {}
        self.acceptance_level = self.params.get('acceptance_level')

    def gather_acceptance_facts(self):
        for host in self.hosts:
            self.hosts_facts[host.name] = dict(level='', error='NA')
            host_image_config_mgr = host.configManager.imageConfigManager
            if host_image_config_mgr:
                try:
                    self.hosts_facts[host.name]['level'] = host_image_config_mgr.HostImageConfigGetAcceptance()
                except vim.fault.HostConfigFault as e:
                    self.hosts_facts[host.name]['error'] = to_native(e.msg)

    def set_acceptance_level(self):
        change = []
        for host in self.hosts:
            host_changed = False
            if self.hosts_facts[host.name]['level'] != self.acceptance_level:
                host_image_config_mgr = host.configManager.imageConfigManager
                if host_image_config_mgr:
                    try:
                        if self.module.check_mode:
                            self.hosts_facts[host.name]['level'] = self.acceptance_level
                        else:
                            host_image_config_mgr.UpdateHostImageAcceptanceLevel(newAcceptanceLevel=self.acceptance_level)
                            self.hosts_facts[host.name]['level'] = host_image_config_mgr.HostImageConfigGetAcceptance()
                        host_changed = True
                    except vim.fault.HostConfigFault as e:
                        self.hosts_facts[host.name]['error'] = to_native(e.msg)

            change.append(host_changed)
        self.module.exit_json(changed=any(change), facts=self.hosts_facts)

    def check_acceptance_state(self):
        self.gather_acceptance_facts()
        if self.desired_state == 'list':
            self.module.exit_json(changed=False, facts=self.hosts_facts)
        self.set_acceptance_level()


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        acceptance_level=dict(type='str',
                              choices=['community', 'partner', 'vmware_accepted', 'vmware_certified']
                              ),
        state=dict(type='str',
                   choices=['list', 'present'],
                   default='list'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        required_if=[
            ['state', 'present', ['acceptance_level']],
        ],
        supports_check_mode=True
    )

    vmware_host_accept_config = VMwareAccpetanceManager(module)
    vmware_host_accept_config.check_acceptance_state()


if __name__ == "__main__":
    main()

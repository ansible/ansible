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
module: vmware_host_ntp
short_description: Manage NTP configurations about an ESXi host
description:
- This module can be used to manage NTP configuration information about an ESXi host.
- User can specify an ESXi hostname or Cluster name. In case of cluster name, all ESXi hosts are updated.
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
    - NTP settings are applied to every ESXi host system in the given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname.
    - NTP settings are applied to this ESXi host system.
    - If C(cluster_name) is not given, this parameter is required.
  ntp_servers:
    description:
    - "IP or FQDN of NTP server/s."
    - This accepts a list of NTP servers. For multiple servers, please look at the examples.
    required: True
  state:
    description:
    - "present: Add NTP server/s, if it specified server/s are absent else do nothing."
    - "absent: Remove NTP server/s, if specified server/s are present else do nothing."
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Set NTP setting for all ESXi Host in given Cluster
  vmware_host_ntp:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
    state: present
    ntp_servers:
        - 0.pool.ntp.org
        - 1.pool.ntp.org

- name: Set NTP setting for an ESXi Host
  vmware_host_ntp:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: present
    ntp_servers:
        - 0.pool.ntp.org
        - 1.pool.ntp.org

- name: Remove NTP setting for an ESXi Host
  vmware_host_ntp:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: absent
    ntp_servers:
        - bad.server.ntp.org
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


class VmwareNtpConfigManager(PyVmomi):
    def __init__(self, module):
        super(VmwareNtpConfigManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.ntp_servers = self.params.get('ntp_servers', list())
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        self.results = {}
        self.desired_state = module.params['state']

    def update_ntp_servers(self, host, ntp_servers, operation='add'):
        changed = False
        host_date_time_manager = host.configManager.dateTimeSystem
        if host_date_time_manager:
            available_ntp_servers = host_date_time_manager.dateTimeInfo.ntpConfig.server
            if operation == 'add':
                available_ntp_servers = available_ntp_servers + ntp_servers
            elif operation == 'delete':
                for server in ntp_servers:
                    if server in available_ntp_servers:
                        available_ntp_servers.remove(server)

            ntp_config_spec = vim.host.NtpConfig()
            ntp_config_spec.server = available_ntp_servers
            date_config_spec = vim.host.DateTimeConfig()
            date_config_spec.ntpConfig = ntp_config_spec
            try:
                host_date_time_manager.UpdateDateTimeConfig(date_config_spec)
                self.results[host.name]['after_change_ntp_servers'] = host_date_time_manager.dateTimeInfo.ntpConfig.server
                changed = True
            except vim.fault.HostConfigFault as e:
                self.results[host.name]['error'] = to_native(e.msg)
            except Exception as e:
                self.results[host.name]['error'] = to_native(e)

        return changed

    def check_host_state(self):
        change_list = []
        changed = False
        for host in self.hosts:
            ntp_servers_to_change = self.check_ntp_servers(host=host)
            self.results[host.name].update(dict(
                ntp_servers_to_change=ntp_servers_to_change,
                desired_state=self.desired_state,
            )
            )

            if not ntp_servers_to_change:
                change_list.append(False)
                self.results[host.name]['current_state'] = self.desired_state
            elif ntp_servers_to_change:
                if self.desired_state == 'present':
                    changed = self.update_ntp_servers(host=host, ntp_servers=ntp_servers_to_change)
                    change_list.append(changed)
                elif self.desired_state == 'absent':
                    changed = self.update_ntp_servers(host=host, ntp_servers=ntp_servers_to_change, operation='delete')
                    change_list.append(changed)
                self.results[host.name]['current_state'] = self.desired_state

        if any(change_list):
            changed = True
        self.module.exit_json(changed=changed, results=self.results)

    def check_ntp_servers(self, host):
        update_ntp_list = []
        host_datetime_system = host.configManager.dateTimeSystem
        if host_datetime_system:
            ntp_servers = host_datetime_system.dateTimeInfo.ntpConfig.server
            self.results[host.name] = dict(available_ntp_servers=ntp_servers)
            for ntp_server in self.ntp_servers:
                if self.desired_state == 'present' and ntp_server not in ntp_servers:
                    update_ntp_list.append(ntp_server)
                if self.desired_state == 'absent' and ntp_server in ntp_servers:
                    update_ntp_list.append(ntp_server)
        return update_ntp_list


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        ntp_servers=dict(type='list', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ]
    )

    vmware_host_ntp_config = VmwareNtpConfigManager(module)
    vmware_host_ntp_config.check_host_state()


if __name__ == "__main__":
    main()

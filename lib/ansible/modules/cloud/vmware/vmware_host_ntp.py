#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
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
short_description: Manage NTP server configuration of an ESXi host
description:
- This module can be used to configure, add or remove NTP servers from an ESXi host.
- If C(state) is not given, the NTP servers will be configured in the exact sequence.
- User can specify an ESXi hostname or Cluster name. In case of cluster name, all ESXi hosts are updated.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - This parameter is required if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - This parameter is required if C(esxi_hostname) is not specified.
    type: str
  ntp_servers:
    description:
    - "IP or FQDN of NTP server(s)."
    - This accepts a list of NTP servers. For multiple servers, please look at the examples.
    type: list
    required: True
  state:
    description:
    - "present: Add NTP server(s), if specified server(s) are absent else do nothing."
    - "absent: Remove NTP server(s), if specified server(s) are present else do nothing."
    - Specified NTP server(s) will be configured if C(state) isn't specified.
    choices: [ present, absent ]
    type: str
  verbose:
    description:
    - Verbose output of the configuration change.
    - Explains if an NTP server was added, removed, or if the NTP server sequence was changed.
    type: bool
    required: false
    default: false
    version_added: 2.8
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Configure NTP servers for an ESXi Host
  vmware_host_ntp:
    hostname: vcenter01.example.local
    username: administrator@vsphere.local
    password: SuperSecretPassword
    esxi_hostname: esx01.example.local
    ntp_servers:
        - 0.pool.ntp.org
        - 1.pool.ntp.org
  delegate_to: localhost

- name: Set NTP servers for all ESXi Host in given Cluster
  vmware_host_ntp:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
    state: present
    ntp_servers:
        - 0.pool.ntp.org
        - 1.pool.ntp.org
  delegate_to: localhost

- name: Set NTP servers for an ESXi Host
  vmware_host_ntp:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: present
    ntp_servers:
        - 0.pool.ntp.org
        - 1.pool.ntp.org
  delegate_to: localhost

- name: Remove NTP servers for an ESXi Host
  vmware_host_ntp:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: absent
    ntp_servers:
        - bad.server.ntp.org
  delegate_to: localhost
'''

RETURN = r'''
results:
    description: metadata about host system's NTP configuration
    returned: always
    type: dict
    sample: {
        "esx01.example.local": {
            "ntp_servers_changed": ["time1.example.local", "time2.example.local", "time3.example.local", "time4.example.local"],
            "ntp_servers": ["time3.example.local", "time4.example.local"],
            "ntp_servers_previous": ["time1.example.local", "time2.example.local"],
        },
        "esx02.example.local": {
            "ntp_servers_changed": ["time3.example.local"],
            "ntp_servers_current": ["time1.example.local", "time2.example.local", "time3.example.local"],
            "state": "present",
            "ntp_servers_previous": ["time1.example.local", "time2.example.local"],
        },
    }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


class VmwareNtpConfigManager(PyVmomi):
    """Class to manage configured NTP servers"""

    def __init__(self, module):
        super(VmwareNtpConfigManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.ntp_servers = self.params.get('ntp_servers', list())
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system.")
        self.results = {}
        self.desired_state = self.params.get('state', None)
        self.verbose = module.params.get('verbose', False)

    def update_ntp_servers(self, host, ntp_servers_configured, ntp_servers_to_change, operation='overwrite'):
        """Update NTP server configuration"""
        host_date_time_manager = host.configManager.dateTimeSystem
        if host_date_time_manager:
            # Prepare new NTP server list
            if operation == 'overwrite':
                new_ntp_servers = list(ntp_servers_to_change)
            else:
                new_ntp_servers = list(ntp_servers_configured)
                if operation == 'add':
                    new_ntp_servers = new_ntp_servers + ntp_servers_to_change
                elif operation == 'delete':
                    for server in ntp_servers_to_change:
                        if server in new_ntp_servers:
                            new_ntp_servers.remove(server)

            # build verbose message
            if self.verbose:
                message = self.build_changed_message(
                    ntp_servers_configured,
                    new_ntp_servers,
                    ntp_servers_to_change,
                    operation
                )

            ntp_config_spec = vim.host.NtpConfig()
            ntp_config_spec.server = new_ntp_servers
            date_config_spec = vim.host.DateTimeConfig()
            date_config_spec.ntpConfig = ntp_config_spec
            try:
                if not self.module.check_mode:
                    host_date_time_manager.UpdateDateTimeConfig(date_config_spec)
                if self.verbose:
                    self.results[host.name]['msg'] = message
            except vim.fault.HostConfigFault as config_fault:
                self.module.fail_json(
                    msg="Failed to configure NTP for host '%s' due to : %s" %
                    (host.name, to_native(config_fault.msg))
                )

            return new_ntp_servers

    def check_host_state(self):
        """Check ESXi host configuration"""
        change_list = []
        changed = False
        for host in self.hosts:
            self.results[host.name] = dict()
            ntp_servers_configured, ntp_servers_to_change = self.check_ntp_servers(host=host)
            # add/remove NTP servers
            if self.desired_state:
                self.results[host.name]['state'] = self.desired_state
                if ntp_servers_to_change:
                    self.results[host.name]['ntp_servers_changed'] = ntp_servers_to_change
                    operation = 'add' if self.desired_state == 'present' else 'delete'
                    new_ntp_servers = self.update_ntp_servers(
                        host=host,
                        ntp_servers_configured=ntp_servers_configured,
                        ntp_servers_to_change=ntp_servers_to_change,
                        operation=operation
                    )
                    self.results[host.name]['ntp_servers_current'] = new_ntp_servers
                    self.results[host.name]['changed'] = True
                    change_list.append(True)
                else:
                    self.results[host.name]['ntp_servers_current'] = ntp_servers_configured
                    if self.verbose:
                        self.results[host.name]['msg'] = (
                            "NTP servers already added" if self.desired_state == 'present'
                            else "NTP servers already removed"
                        )
                    self.results[host.name]['changed'] = False
                    change_list.append(False)
            # overwrite NTP servers
            else:
                self.results[host.name]['ntp_servers'] = self.ntp_servers
                if ntp_servers_to_change:
                    self.results[host.name]['ntp_servers_changed'] = self.get_differt_entries(
                        ntp_servers_configured,
                        ntp_servers_to_change
                    )
                    self.update_ntp_servers(
                        host=host,
                        ntp_servers_configured=ntp_servers_configured,
                        ntp_servers_to_change=ntp_servers_to_change,
                        operation='overwrite'
                    )
                    self.results[host.name]['changed'] = True
                    change_list.append(True)
                else:
                    if self.verbose:
                        self.results[host.name]['msg'] = "NTP servers already configured"
                    self.results[host.name]['changed'] = False
                    change_list.append(False)

        if any(change_list):
            changed = True
        self.module.exit_json(changed=changed, results=self.results)

    def check_ntp_servers(self, host):
        """Check configured NTP servers"""
        update_ntp_list = []
        host_datetime_system = host.configManager.dateTimeSystem
        if host_datetime_system:
            ntp_servers_configured = host_datetime_system.dateTimeInfo.ntpConfig.server
            # add/remove NTP servers
            if self.desired_state:
                for ntp_server in self.ntp_servers:
                    if self.desired_state == 'present' and ntp_server not in ntp_servers_configured:
                        update_ntp_list.append(ntp_server)
                    if self.desired_state == 'absent' and ntp_server in ntp_servers_configured:
                        update_ntp_list.append(ntp_server)
            # overwrite NTP servers
            else:
                if ntp_servers_configured != self.ntp_servers:
                    for ntp_server in self.ntp_servers:
                        update_ntp_list.append(ntp_server)
            if update_ntp_list:
                self.results[host.name]['ntp_servers_previous'] = ntp_servers_configured

        return ntp_servers_configured, update_ntp_list

    def build_changed_message(self, ntp_servers_configured, new_ntp_servers, ntp_servers_to_change, operation):
        """Build changed message"""
        check_mode = 'would be ' if self.module.check_mode else ''
        if operation == 'overwrite':
            # get differences
            add = self.get_not_in_list_one(new_ntp_servers, ntp_servers_configured)
            remove = self.get_not_in_list_one(ntp_servers_configured, new_ntp_servers)
            diff_servers = list(ntp_servers_configured)
            if add and remove:
                for server in add:
                    diff_servers.append(server)
                for server in remove:
                    diff_servers.remove(server)
                if new_ntp_servers != diff_servers:
                    message = (
                        "NTP server %s %sadded and %s %sremoved and the server sequence %schanged as well" %
                        (self.array_to_string(add), check_mode, self.array_to_string(remove), check_mode, check_mode)
                    )
                else:
                    if new_ntp_servers != ntp_servers_configured:
                        message = (
                            "NTP server %s %sreplaced with %s" %
                            (self.array_to_string(remove), check_mode, self.array_to_string(add))
                        )
                    else:
                        message = (
                            "NTP server %s %sremoved and %s %sadded" %
                            (self.array_to_string(remove), check_mode, self.array_to_string(add), check_mode)
                        )
            elif add:
                for server in add:
                    diff_servers.append(server)
                if new_ntp_servers != diff_servers:
                    message = (
                        "NTP server %s %sadded and the server sequence %schanged as well" %
                        (self.array_to_string(add), check_mode, check_mode)
                    )
                else:
                    message = "NTP server %s %sadded" % (self.array_to_string(add), check_mode)
            elif remove:
                for server in remove:
                    diff_servers.remove(server)
                if new_ntp_servers != diff_servers:
                    message = (
                        "NTP server %s %sremoved and the server sequence %schanged as well" %
                        (self.array_to_string(remove), check_mode, check_mode)
                    )
                else:
                    message = "NTP server %s %sremoved" % (self.array_to_string(remove), check_mode)
            else:
                message = "NTP server sequence %schanged" % check_mode
        elif operation == 'add':
            message = "NTP server %s %sadded" % (self.array_to_string(ntp_servers_to_change), check_mode)
        elif operation == 'delete':
            message = "NTP server %s %sremoved" % (self.array_to_string(ntp_servers_to_change), check_mode)

        return message

    @staticmethod
    def get_not_in_list_one(list1, list2):
        """Return entries that ore not in list one"""
        return [x for x in list1 if x not in set(list2)]

    @staticmethod
    def array_to_string(array):
        """Return string from array"""
        if len(array) > 2:
            string = (
                ', '.join("'{0}'".format(element) for element in array[:-1]) + ', and '
                + "'{0}'".format(str(array[-1]))
            )
        elif len(array) == 2:
            string = ' and '.join("'{0}'".format(element) for element in array)
        elif len(array) == 1:
            string = "'{0}'".format(array[0])
        return string

    @staticmethod
    def get_differt_entries(list1, list2):
        """Return different entries of two lists"""
        return [a for a in list1 + list2 if (a not in list1) or (a not in list2)]


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        ntp_servers=dict(type='list', required=True),
        state=dict(type='str', choices=['absent', 'present']),
        verbose=dict(type='bool', default=False, required=False)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        supports_check_mode=True
    )

    vmware_host_ntp_config = VmwareNtpConfigManager(module)
    vmware_host_ntp_config.check_host_state()


if __name__ == "__main__":
    main()

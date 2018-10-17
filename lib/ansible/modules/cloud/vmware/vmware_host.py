#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017, Ansible Project
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
module: vmware_host
short_description: Add / Remove ESXi host to / from vCenter
description:
- This module can be used to add / remove / reconnect an ESXi host to / from vCenter.
version_added: '2.0'
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Maxime de Roucy (@tchernomax)
notes:
- Tested on vSphere 5.5, 6.0 and 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  datacenter_name:
    description:
    - Name of the datacenter to add the host.
    - Aliases added in version 2.6.
    required: yes
    aliases: ['datacenter']
  cluster_name:
    description:
    - Name of the cluster to add the host.
    - If C(folder) is not set, then this parameter is required.
    - Aliases added in version 2.6.
    aliases: ['cluster']
  folder:
    description:
    - Name of the folder under which host to add.
    - If C(cluster_name) is not set, then this parameter is required.
    - "For example, if there is a datacenter 'dc1' under folder called 'Site1' then, this value will be '/Site1/dc1/host'."
    - "Here 'host' is an invisible folder under VMware Web Client."
    - "Another example, if there is a nested folder structure like '/myhosts/india/pune' under
       datacenter 'dc2', then C(folder) value will be '/dc2/host/myhosts/india/pune'."
    - "Other Examples: "
    - "  - '/Site2/dc2/Asia-Cluster/host'"
    - "  - '/dc3/Asia-Cluster/host'"
    version_added: "2.6"
  add_connected:
    description:
    - If set to C(True), then the host should be connected as soon as it is added.
    - This parameter is ignored if state is set to a value other than C(present).
    default: True
    type: 'bool'
    version_added: "2.6"
  esxi_hostname:
    description:
    - ESXi hostname to manage.
    required: yes
  esxi_username:
    description:
    - ESXi username.
    - Required for adding a host.
    - Optional for reconnect.
    - Unused for removing.
    - No longer a required parameter from version 2.5.
  esxi_password:
    description:
    - ESXi password.
    - Required for adding a host.
    - Optional for reconnect.
    - Unused for removing.
    - No longer a required parameter from version 2.5.
  state:
    description:
    - If set to C(present), then add the host if host is absent.
    - If set to C(present), then do nothing if host already exists.
    - If set to C(absent), then remove the host if host is present.
    - If set to C(absent), then do nothing if host already does not exists.
    - If set to C(add_or_reconnect), then add the host if it's absent else reconnect it.
    - If set to C(reconnect), then reconnect the host if it's present else fail.
    default: present
    choices: ['present', 'absent', 'add_or_reconnect', 'reconnect']
  esxi_ssl_thumbprint:
    description:
    - "Specifying the hostsystem certificate's thumbprint."
    - "Use following command to get hostsystem certificate's thumbprint - "
    - "# openssl x509 -in /etc/vmware/ssl/rui.crt -fingerprint -sha1 -noout"
    version_added: 2.5
    default: ''
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Add ESXi Host to vCenter
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter_name
    cluster_name: cluster_name
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    state: present

- name: Add ESXi Host to vCenter under a specific folder
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter_name
    folder: '/Site2/Asia-Cluster/host'
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    state: present
    add_connected: True

- name: Reconnect ESXi Host (with username/password set)
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter_name
    cluster_name: cluster_name
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    state: reconnect

- name: Reconnect ESXi Host (with default username/password)
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter_name
    cluster_name: cluster_name
    esxi_hostname: '{{ esxi_hostname }}'
    state: reconnect

- name: Add ESXi Host with SSL Thumbprint to vCenter
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter_name
    cluster_name: cluster_name
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    esxi_ssl_thumbprint: "3C:A5:60:6F:7A:B7:C4:6C:48:28:3D:2F:A5:EC:A3:58:13:88:F6:DD"
    state: present
'''

RETURN = r'''
result:
    description: metadata about the new host system added
    returned: on successful addition
    type: str
    sample: "'vim.ComputeResource:domain-s222'"
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (PyVmomi, TaskError, vmware_argument_spec,
                                         wait_for_task, find_host_by_cluster_datacenter)


class VMwareHost(PyVmomi):
    def __init__(self, module):
        super(VMwareHost, self).__init__(module)
        self.datacenter_name = module.params['datacenter_name']
        self.cluster_name = module.params['cluster_name']
        self.folder_name = module.params['folder']
        self.esxi_hostname = module.params['esxi_hostname']
        self.esxi_username = module.params['esxi_username']
        self.esxi_password = module.params['esxi_password']
        self.state = module.params['state']
        self.esxi_ssl_thumbprint = module.params.get('esxi_ssl_thumbprint', '')
        self.cluster = self.folder = self.host = None

    def process_state(self):
        # Currently state_update_host is not implemented.
        host_states = {
            'absent': {
                'present': self.state_remove_host,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_exit_unchanged,
                'absent': self.state_add_host,
            },
            'add_or_reconnect': {
                'present': self.state_reconnect_host,
                'absent': self.state_add_host,
            },
            'reconnect': {
                'present': self.state_reconnect_host,
            }
        }

        try:
            host_states[self.state][self.check_host_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def get_host_connect_spec(self):
        """
        Function to return Host connection specification
        Returns: host connection specification

        """
        host_connect_spec = vim.host.ConnectSpec()
        host_connect_spec.hostName = self.esxi_hostname
        host_connect_spec.userName = self.esxi_username
        host_connect_spec.password = self.esxi_password
        host_connect_spec.force = True
        host_connect_spec.sslThumbprint = self.esxi_ssl_thumbprint
        return host_connect_spec

    def add_host_to_vcenter(self):
        host_connect_spec = self.get_host_connect_spec()
        as_connected = self.params.get('add_connected')
        esxi_license = None
        resource_pool = None

        for count in range(0, 2):
            try:
                task = None
                if self.folder:
                    task = self.folder.AddStandaloneHost(spec=host_connect_spec, addConnected=as_connected)
                elif self.cluster:
                    task = self.cluster.AddHost_Task(host_connect_spec, as_connected, resource_pool, esxi_license)
                success, result = wait_for_task(task)
                return success, result
            except TaskError as task_error_exception:
                task_error = task_error_exception.args[0]
                if self.esxi_ssl_thumbprint == '' and isinstance(task_error, vim.fault.SSLVerifyFault):
                    # User has not specified SSL Thumbprint for ESXi host,
                    # try to grab it using SSLVerifyFault exception
                    host_connect_spec.sslThumbprint = task_error.thumbprint
                else:
                    self.module.fail_json(msg="Failed to add host %s to vCenter: %s" % (self.esxi_hostname,
                                                                                        to_native(task_error.msg)))
            except vmodl.fault.NotSupported:
                self.module.fail_json(msg="Failed to add host %s to vCenter as host is"
                                          " being added to a folder %s whose childType"
                                          " property does not contain"
                                          " \"ComputeResource\"." % (self.esxi_hostname, self.folder_name))
            except Exception as generic_exc:
                self.module.fail_json(msg="Failed to add host %s to vCenter: %s" % (self.esxi_hostname,
                                                                                    to_native(generic_exc)))

        self.module.fail_json(msg="Failed to add host %s to vCenter" % self.esxi_hostname)

    def reconnect_host_to_vcenter(self):
        reconnecthost_args = {}
        reconnecthost_args['reconnectSpec'] = vim.HostSystem.ReconnectSpec()
        reconnecthost_args['reconnectSpec'].syncState = True

        if self.esxi_username is not None or self.esxi_password is not None:
            reconnecthost_args['cnxSpec'] = self.get_host_connect_spec()

            for count in range(0, 2):
                try:
                    task = self.host.ReconnectHost_Task(**reconnecthost_args)
                    success, result = wait_for_task(task)
                    return success, result
                except TaskError as task_error_exception:
                    task_error = task_error_exception.args[0]
                    if self.esxi_ssl_thumbprint == '' and isinstance(task_error, vim.fault.SSLVerifyFault):
                        # User has not specified SSL Thumbprint for ESXi host,
                        # try to grab it using SSLVerifyFault exception
                        reconnecthost_args['cnxSpec'].sslThumbprint = task_error.thumbprint
                    else:
                        self.module.fail_json(msg="Failed to reconnect host %s to vCenter: %s" % (self.esxi_hostname,
                                                                                                  to_native(task_error.msg)))
            self.module.fail_json(msg="Failed to reconnect host %s to vCenter" % self.esxi_hostname)
        else:
            try:
                task = self.host.ReconnectHost_Task(**reconnecthost_args)
                success, result = wait_for_task(task)
                return success, result
            except TaskError as task_error_exception:
                task_error = task_error_exception.args[0]
                self.module.fail_json(msg="Failed to reconnect host %s to vCenter due to %s" % (self.esxi_hostname,
                                                                                                to_native(task_error.msg)))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_remove_host(self):
        changed = True
        result = None
        if not self.module.check_mode:
            if not self.host.runtime.inMaintenanceMode:
                maintenance_mode_task = self.host.EnterMaintenanceMode_Task(300, True, None)
                changed, result = wait_for_task(maintenance_mode_task)

            if changed:
                task = self.host.Destroy_Task()
                changed, result = wait_for_task(task)
            else:
                raise Exception(result)
        self.module.exit_json(changed=changed, result=str(result))

    def state_update_host(self):
        self.module.exit_json(changed=False, msg="Currently not implemented.")

    def state_add_host(self):
        changed = True
        result = None

        if not self.module.check_mode:
            changed, result = self.add_host_to_vcenter()
        self.module.exit_json(changed=changed, result=str(result))

    def state_reconnect_host(self):
        changed = True
        result = None

        if not self.module.check_mode:
            changed, result = self.reconnect_host_to_vcenter()
        self.module.exit_json(changed=changed, result=str(result))

    def check_host_state(self):
        if self.cluster_name:
            self.host, self.cluster = find_host_by_cluster_datacenter(self.module, self.content,
                                                                      self.datacenter_name, self.cluster_name,
                                                                      self.esxi_hostname)
        elif self.folder_name:
            si = self.content.searchIndex
            folder_obj = si.FindByInventoryPath(self.folder_name)
            if folder_obj and isinstance(folder_obj, vim.Folder):
                self.folder = folder_obj

            if self.folder is None:
                self.module.fail_json(msg="Failed to get host system details from"
                                          " the given folder %s" % self.folder_name,
                                      details="This could either mean that the value of folder is"
                                              " invalid or the provided folder does not exists.")
            for child in self.folder.childEntity:
                if child and isinstance(child, vim.HostSystem) and child.name == self.esxi_hostname:
                    self.host = child

        if self.host is None:
            return 'absent'
        else:
            return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter_name=dict(type='str', required=True, aliases=['datacenter']),
        cluster_name=dict(type='str', aliases=['cluster']),
        esxi_hostname=dict(type='str', required=True),
        esxi_username=dict(type='str'),
        esxi_password=dict(type='str', no_log=True),
        esxi_ssl_thumbprint=dict(type='str', default=''),
        state=dict(default='present',
                   choices=['present', 'absent', 'add_or_reconnect', 'reconnect'],
                   type='str'),
        folder=dict(type='str'),
        add_connected=dict(type='bool', default=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['esxi_username', 'esxi_password']],
            ['state', 'add_or_reconnect', ['esxi_username', 'esxi_password']]
        ],
        required_one_of=[
            ['cluster_name', 'folder'],
        ],
        mutually_exclusive=[
            ['cluster_name', 'folder'],
        ]
    )

    vmware_host = VMwareHost(module)
    vmware_host.process_state()


if __name__ == '__main__':
    main()

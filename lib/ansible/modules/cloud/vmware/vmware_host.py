#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017, Ansible Project
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
module: vmware_host
short_description: Add, remove, or move an ESXi host to, from, or within vCenter
description:
- This module can be used to add, reconnect, or remove an ESXi host to or from vCenter.
- This module can also be used to move an ESXi host to a cluster or folder, or vice versa, within the same datacenter.
version_added: '2.0'
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Maxime de Roucy (@tchernomax)
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 5.5, 6.0, 6.5 and 6.7
requirements:
- python >= 2.6
- PyVmomi
- ssl
- socket
- hashlib
options:
  datacenter_name:
    description:
    - Name of the datacenter to add the host.
    - Aliases added in version 2.6.
    required: yes
    aliases: ['datacenter']
    type: str
  cluster_name:
    description:
    - Name of the cluster to add the host.
    - If C(folder) is not set, then this parameter is required.
    - Aliases added in version 2.6.
    aliases: ['cluster']
    type: str
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
    aliases: ['folder_name']
    type: str
  add_connected:
    description:
    - If set to C(True), then the host should be connected as soon as it is added.
    - This parameter is ignored if state is set to a value other than C(present).
    default: True
    type: bool
    version_added: "2.6"
  esxi_hostname:
    description:
    - ESXi hostname to manage.
    required: yes
    type: str
  esxi_username:
    description:
    - ESXi username.
    - Required for adding a host.
    - Optional for reconnect. If both C(esxi_username) and C(esxi_password) are used
    - Unused for removing.
    - No longer a required parameter from version 2.5.
    type: str
  esxi_password:
    description:
    - ESXi password.
    - Required for adding a host.
    - Optional for reconnect.
    - Unused for removing.
    - No longer a required parameter from version 2.5.
    type: str
  state:
    description:
    - If set to C(present), add the host if host is absent.
    - If set to C(present), update the location of the host if host already exists.
    - If set to C(absent), remove the host if host is present.
    - If set to C(absent), do nothing if host already does not exists.
    - If set to C(add_or_reconnect), add the host if it's absent else reconnect it and update the location.
    - If set to C(reconnect), then reconnect the host if it's present and update the location.
    default: present
    choices: ['present', 'absent', 'add_or_reconnect', 'reconnect']
    type: str
  esxi_ssl_thumbprint:
    description:
    - "Specifying the hostsystem certificate's thumbprint."
    - "Use following command to get hostsystem certificate's thumbprint - "
    - "# openssl x509 -in /etc/vmware/ssl/rui.crt -fingerprint -sha1 -noout"
    - Only used if C(fetch_thumbprint) isn't set to C(true).
    version_added: 2.5
    default: ''
    type: str
    aliases: ['ssl_thumbprint']
  fetch_ssl_thumbprint:
    description:
    - Fetch the thumbprint of the host's SSL certificate.
    - This basically disables the host certificate verification (check if it was signed by a recognized CA).
    - Disable this option if you want to allow only hosts with valid certificates to be added to vCenter.
    - If this option is set to C(false) and the certificate can't be verified, an add or reconnect will fail.
    - Unused when C(esxi_ssl_thumbprint) is set.
    - Optional for reconnect, but only used if C(esxi_username) and C(esxi_password) are used.
    - Unused for removing.
    type: bool
    version_added: 2.8
    default: True
  force_connection:
    description:
    - Force the connection if the host is already being managed by another vCenter server.
    type: bool
    version_added: 2.8
    default: True
  reconnect_disconnected:
    description:
    - Reconnect disconnected hosts.
    - This is only used if C(state) is set to C(present) and if the host already exists.
    type: bool
    version_added: 2.8
    default: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Add ESXi Host to vCenter
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    cluster: cluster_name
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    state: present
  delegate_to: localhost

- name: Add ESXi Host to vCenter under a specific folder
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    folder: '/Site2/Asia-Cluster/host'
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    state: present
    add_connected: True
  delegate_to: localhost

- name: Reconnect ESXi Host (with username/password set)
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    cluster: cluster_name
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    state: reconnect
  delegate_to: localhost

- name: Reconnect ESXi Host (with default username/password)
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    cluster: cluster_name
    esxi_hostname: '{{ esxi_hostname }}'
    state: reconnect
  delegate_to: localhost

- name: Add ESXi Host with SSL Thumbprint to vCenter
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    cluster: cluster_name
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    esxi_ssl_thumbprint: "3C:A5:60:6F:7A:B7:C4:6C:48:28:3D:2F:A5:EC:A3:58:13:88:F6:DD"
    state: present
  delegate_to: localhost
'''

RETURN = r'''
result:
    description: metadata about the new host system added
    returned: on successful addition
    type: str
    sample: "Host already connected to vCenter 'vcenter01' in cluster 'cluster01'"
'''

try:
    from pyVmomi import vim, vmodl
    import ssl
    import socket
    import hashlib
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (
    PyVmomi, TaskError, vmware_argument_spec,
    wait_for_task, find_host_by_cluster_datacenter, find_hostsystem_by_name
)


class VMwareHost(PyVmomi):
    """Class to manage vCenter connection"""
    def __init__(self, module):
        super(VMwareHost, self).__init__(module)
        self.vcenter = module.params['hostname']
        self.datacenter_name = module.params['datacenter_name']
        self.cluster_name = module.params['cluster_name']
        self.folder_name = module.params['folder']
        self.esxi_hostname = module.params['esxi_hostname']
        self.esxi_username = module.params['esxi_username']
        self.esxi_password = module.params['esxi_password']
        self.state = module.params['state']
        self.esxi_ssl_thumbprint = module.params.get('esxi_ssl_thumbprint', '')
        self.force_connection = module.params.get('force_connection')
        self.fetch_ssl_thumbprint = module.params.get('fetch_ssl_thumbprint')
        self.reconnect_disconnected = module.params.get('reconnect_disconnected')
        self.host_update = self.host = self.cluster = self.folder = self.host_parent_compute_resource = None

    def process_state(self):
        """Check the current state"""
        host_states = {
            'absent': {
                'present': self.state_remove_host,
                'update': self.state_remove_host,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_exit_unchanged,
                'update': self.state_update_host,
                'absent': self.state_add_host,
            },
            'add_or_reconnect': {
                'present': self.state_reconnect_host,
                'update': self.state_update_host,
                'absent': self.state_add_host,
            },
            'reconnect': {
                'present': self.state_reconnect_host,
                'update': self.state_update_host,
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

    def check_host_state(self):
        """Check current state"""
        # Check if the host is already connected to vCenter
        self.host_update = find_hostsystem_by_name(self.content, self.esxi_hostname)
        if self.host_update:
            # The host name is unique in vCenter; A host with the same name cannot exist in another datacenter
            # However, the module will fail later if the target folder/cluster is in another datacenter as the host
            # Check if the host is connected under the target cluster
            if self.cluster_name:
                self.host, self.cluster = self.search_cluster(self.datacenter_name, self.cluster_name, self.esxi_hostname)
                if self.host:
                    state = 'present'
                else:
                    state = 'update'
            # Check if the host is connected under the target folder
            elif self.folder_name:
                self.folder = self.search_folder(self.folder_name)
                for child in self.folder.childEntity:
                    if not child or not isinstance(child, vim.ComputeResource):
                        continue
                    try:
                        if isinstance(child.host[0], vim.HostSystem) and child.name == self.esxi_hostname:
                            self.host_parent_compute_resource = child
                            self.host = child.host[0]
                            break
                    except IndexError:
                        continue
                if self.host:
                    state = 'present'
                else:
                    state = 'update'
        else:
            state = 'absent'
        return state

    def search_folder(self, folder_name):
        """
            Search folder in vCenter
            Returns: folder object
        """
        search_index = self.content.searchIndex
        folder_obj = search_index.FindByInventoryPath(folder_name)
        if not (folder_obj and isinstance(folder_obj, vim.Folder)):
            self.module.fail_json(msg="Folder '%s' not found" % folder_name)
        return folder_obj

    def search_cluster(self, datacenter_name, cluster_name, esxi_hostname):
        """
            Search cluster in vCenter
            Returns: host and cluster object
        """
        return find_host_by_cluster_datacenter(
            self.module, self.content, datacenter_name, cluster_name, esxi_hostname
        )

    def state_exit_unchanged(self):
        """Exit with status message"""
        if not self.host_update:
            result = "Host already disconnected"
        elif self.reconnect_disconnected and self.host_update.runtime.connectionState == 'disconnected':
            self.state_reconnect_host()
        else:
            if self.folder_name:
                result = "Host already connected to vCenter '%s' in folder '%s'" % (self.vcenter, self.folder_name)
            elif self.cluster_name:
                result = "Host already connected to vCenter '%s' in cluster '%s'" % (self.vcenter, self.cluster_name)
        self.module.exit_json(changed=False, result=str(result))

    def state_add_host(self):
        """Add ESXi host to a cluster of folder in vCenter"""
        changed = True
        result = None

        if self.module.check_mode:
            result = "Host would be connected to vCenter '%s'" % self.vcenter
        else:
            host_connect_spec = self.get_host_connect_spec()
            as_connected = self.params.get('add_connected')
            esxi_license = None
            resource_pool = None
            task = None
            if self.folder_name:
                self.folder = self.search_folder(self.folder_name)
                try:
                    task = self.folder.AddStandaloneHost(
                        spec=host_connect_spec, compResSpec=resource_pool,
                        addConnected=as_connected, license=esxi_license
                    )
                except vim.fault.InvalidLogin as invalid_login:
                    self.module.fail_json(
                        msg="Cannot authenticate with the host : %s" % to_native(invalid_login)
                    )
                except vim.fault.HostConnectFault as connect_fault:
                    self.module.fail_json(
                        msg="An error occurred during connect : %s" % to_native(connect_fault)
                    )
                except vim.fault.DuplicateName as duplicate_name:
                    self.module.fail_json(
                        msg="The folder already contains a host with the same name : %s" %
                        to_native(duplicate_name)
                    )
                except vmodl.fault.InvalidArgument as invalid_argument:
                    self.module.fail_json(
                        msg="An argument was specified incorrectly : %s" % to_native(invalid_argument)
                    )
                except vim.fault.AlreadyBeingManaged as already_managed:
                    self.module.fail_json(
                        msg="The host is already being managed by another vCenter server : %s" %
                        to_native(already_managed)
                    )
                except vmodl.fault.NotEnoughLicenses as not_enough_licenses:
                    self.module.fail_json(
                        msg="There are not enough licenses to add this host : %s" % to_native(not_enough_licenses)
                    )
                except vim.fault.NoHost as no_host:
                    self.module.fail_json(
                        msg="Unable to contact the host : %s" % to_native(no_host)
                    )
                except vmodl.fault.NotSupported as not_supported:
                    self.module.fail_json(
                        msg="The folder is not a host folder : %s" % to_native(not_supported)
                    )
                except vim.fault.NotSupportedHost as host_not_supported:
                    self.module.fail_json(
                        msg="The host is running a software version that is not supported : %s" %
                        to_native(host_not_supported)
                    )
                except vim.fault.AgentInstallFailed as agent_install:
                    self.module.fail_json(
                        msg="Error during vCenter agent installation : %s" % to_native(agent_install)
                    )
                except vim.fault.AlreadyConnected as already_connected:
                    self.module.fail_json(
                        msg="The host is already connected to the vCenter server : %s" % to_native(already_connected)
                    )
                except vim.fault.SSLVerifyFault as ssl_fault:
                    self.module.fail_json(
                        msg="The host certificate could not be authenticated : %s" % to_native(ssl_fault)
                    )
            elif self.cluster_name:
                self.host, self.cluster = self.search_cluster(
                    self.datacenter_name,
                    self.cluster_name,
                    self.esxi_hostname
                )
                try:
                    task = self.cluster.AddHost_Task(
                        spec=host_connect_spec, asConnected=as_connected,
                        resourcePool=resource_pool, license=esxi_license
                    )
                except vim.fault.InvalidLogin as invalid_login:
                    self.module.fail_json(
                        msg="Cannot authenticate with the host : %s" % to_native(invalid_login)
                    )
                except vim.fault.HostConnectFault as connect_fault:
                    self.module.fail_json(
                        msg="An error occurred during connect : %s" % to_native(connect_fault)
                    )
                except vim.fault.DuplicateName as duplicate_name:
                    self.module.fail_json(
                        msg="The cluster already contains a host with the same name : %s" %
                        to_native(duplicate_name)
                    )
                except vim.fault.AlreadyBeingManaged as already_managed:
                    self.module.fail_json(
                        msg="The host is already being managed by another vCenter server : %s" %
                        to_native(already_managed)
                    )
                except vmodl.fault.NotEnoughLicenses as not_enough_licenses:
                    self.module.fail_json(
                        msg="There are not enough licenses to add this host : %s" % to_native(not_enough_licenses)
                    )
                except vim.fault.NoHost as no_host:
                    self.module.fail_json(
                        msg="Unable to contact the host : %s" % to_native(no_host)
                    )
                except vim.fault.NotSupportedHost as host_not_supported:
                    self.module.fail_json(
                        msg="The host is running a software version that is not supported; "
                        "It may still be possible to add the host as a stand-alone host : %s" %
                        to_native(host_not_supported)
                    )
                except vim.fault.TooManyHosts as too_many_hosts:
                    self.module.fail_json(
                        msg="No additional hosts can be added to the cluster : %s" % to_native(too_many_hosts)
                    )
                except vim.fault.AgentInstallFailed as agent_install:
                    self.module.fail_json(
                        msg="Error during vCenter agent installation : %s" % to_native(agent_install)
                    )
                except vim.fault.AlreadyConnected as already_connected:
                    self.module.fail_json(
                        msg="The host is already connected to the vCenter server : %s" % to_native(already_connected)
                    )
                except vim.fault.SSLVerifyFault as ssl_fault:
                    self.module.fail_json(
                        msg="The host certificate could not be authenticated : %s" % to_native(ssl_fault)
                    )
            try:
                changed, result = wait_for_task(task)
                result = "Host connected to vCenter '%s'" % self.vcenter
            except TaskError as task_error:
                self.module.fail_json(
                    msg="Failed to add host to vCenter '%s' : %s" % (self.vcenter, to_native(task_error))
                )

        self.module.exit_json(changed=changed, result=result)

    def get_host_connect_spec(self):
        """
        Function to return Host connection specification
        Returns: host connection specification
        """
        host_connect_spec = vim.host.ConnectSpec()
        host_connect_spec.hostName = self.esxi_hostname
        host_connect_spec.userName = self.esxi_username
        host_connect_spec.password = self.esxi_password
        host_connect_spec.force = self.force_connection
        # Get the thumbprint of the SSL certificate
        if self.fetch_ssl_thumbprint and self.esxi_ssl_thumbprint == '':
            # We need to grab the thumbprint manually because it's not included in
            # the task error via an SSLVerifyFault exception anymore
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            wrapped_socket = ssl.wrap_socket(sock)
            try:
                wrapped_socket.connect((self.esxi_hostname, 443))
            except socket.error as socket_error:
                self.module.fail_json(msg="Cannot connect to host : %s" % socket_error)
            else:
                der_cert_bin = wrapped_socket.getpeercert(True)
                # thumb_md5 = hashlib.md5(der_cert_bin).hexdigest()
                thumb_sha1 = self.format_number(hashlib.sha1(der_cert_bin).hexdigest())
                # thumb_sha256 = hashlib.sha256(der_cert_bin).hexdigest()
            wrapped_socket.close()
            host_connect_spec.sslThumbprint = thumb_sha1
        else:
            host_connect_spec.sslThumbprint = self.esxi_ssl_thumbprint
        return host_connect_spec

    @staticmethod
    def format_number(number):
        """Format number"""
        string = str(number)
        return ':'.join(a + b for a, b in zip(string[::2], string[1::2]))

    def state_reconnect_host(self):
        """Reconnect host to vCenter"""
        changed = True
        result = None

        if self.module.check_mode:
            result = "Host would be reconnected to vCenter '%s'" % self.vcenter
        else:
            self.reconnect_host(self.host)
            result = "Host reconnected to vCenter '%s'" % self.vcenter
        self.module.exit_json(changed=changed, result=str(result))

    def reconnect_host(self, host_object):
        """Reconnect host to vCenter"""
        reconnecthost_args = {}
        reconnecthost_args['reconnectSpec'] = vim.HostSystem.ReconnectSpec()
        reconnecthost_args['reconnectSpec'].syncState = True

        if self.esxi_username and self.esxi_password:
            # Build the connection spec as well and fetch thumbprint if enabled
            # Useful if you reinstalled a host and it uses a new self-signed certificate
            reconnecthost_args['cnxSpec'] = self.get_host_connect_spec()
        try:
            task = host_object.ReconnectHost_Task(**reconnecthost_args)
        except vim.fault.InvalidLogin as invalid_login:
            self.module.fail_json(
                msg="Cannot authenticate with the host : %s" % to_native(invalid_login)
            )
        except vim.fault.InvalidState as invalid_state:
            self.module.fail_json(
                msg="The host is not disconnected : %s" % to_native(invalid_state)
            )
        except vim.fault.InvalidName as invalid_name:
            self.module.fail_json(
                msg="The host name is invalid : %s" % to_native(invalid_name)
            )
        except vim.fault.HostConnectFault as connect_fault:
            self.module.fail_json(
                msg="An error occurred during reconnect : %s" % to_native(connect_fault)
            )
        except vmodl.fault.NotSupported as not_supported:
            self.module.fail_json(
                msg="No host can be added to this group : %s" % to_native(not_supported)
            )
        except vim.fault.AlreadyBeingManaged as already_managed:
            self.module.fail_json(
                msg="The host is already being managed by another vCenter server : %s" % to_native(already_managed)
            )
        except vmodl.fault.NotEnoughLicenses as not_enough_licenses:
            self.module.fail_json(
                msg="There are not enough licenses to add this host : %s" % to_native(not_enough_licenses)
            )
        except vim.fault.NoHost as no_host:
            self.module.fail_json(
                msg="Unable to contact the host : %s" % to_native(no_host)
            )
        except vim.fault.NotSupportedHost as host_not_supported:
            self.module.fail_json(
                msg="The host is running a software version that is not supported : %s" %
                to_native(host_not_supported)
            )
        except vim.fault.SSLVerifyFault as ssl_fault:
            self.module.fail_json(
                msg="The host certificate could not be authenticated : %s" % to_native(ssl_fault)
            )
        try:
            changed, result = wait_for_task(task)
        except TaskError as task_error:
            self.module.fail_json(
                msg="Failed to reconnect host to vCenter '%s' due to %s" %
                (self.vcenter, to_native(task_error))
            )

    def state_remove_host(self):
        """Remove host from vCenter"""
        changed = True
        result = None
        if self.module.check_mode:
            result = "Host would be removed from vCenter '%s'" % self.vcenter
        else:
            # Check parent type
            parent_type = self.get_parent_type(self.host_update)
            if parent_type == 'cluster':
                self.put_host_in_maintenance_mode(self.host_update)
            try:
                if self.folder_name:
                    task = self.host_parent_compute_resource.Destroy_Task()
                elif self.cluster_name:
                    task = self.host.Destroy_Task()
            except vim.fault.VimFault as vim_fault:
                self.module.fail_json(msg=vim_fault)
            try:
                changed, result = wait_for_task(task)
                result = "Host removed from vCenter '%s'" % self.vcenter
            except TaskError as task_error:
                self.module.fail_json(
                    msg="Failed to remove the host from vCenter '%s' : %s" % (self.vcenter, to_native(task_error))
                )
        self.module.exit_json(changed=changed, result=str(result))

    def put_host_in_maintenance_mode(self, host_object):
        """Put host in maintenance mode, if not already"""
        if not host_object.runtime.inMaintenanceMode:
            try:
                try:
                    maintenance_mode_task = host_object.EnterMaintenanceMode_Task(300, True, None)
                except vim.fault.InvalidState as invalid_state:
                    self.module.fail_json(
                        msg="The host is already in maintenance mode : %s" % to_native(invalid_state)
                    )
                except vim.fault.Timedout as timed_out:
                    self.module.fail_json(
                        msg="The maintenance mode operation timed out : %s" % to_native(timed_out)
                    )
                except vim.fault.Timedout as timed_out:
                    self.module.fail_json(
                        msg="The maintenance mode operation was canceled : %s" % to_native(timed_out)
                    )
                wait_for_task(maintenance_mode_task)
            except TaskError as task_err:
                self.module.fail_json(
                    msg="Failed to put the host in maintenance mode : %s" % to_native(task_err)
                )

    def get_parent_type(self, host_object):
        """
            Get the type of the parent object
            Returns: string with 'folder' or 'cluster'
        """
        object_type = None
        # check 'vim.ClusterComputeResource' first because it's also an
        # instance of 'vim.ComputeResource'
        if isinstance(host_object.parent, vim.ClusterComputeResource):
            object_type = 'cluster'
        elif isinstance(host_object.parent, vim.ComputeResource):
            object_type = 'folder'
        return object_type

    def state_update_host(self):
        """Move host to a cluster or a folder, or vice versa"""
        changed = True
        result = None
        reconnect = False

        # Check if the host is disconnected if reconnect disconnected hosts is true
        if self.reconnect_disconnected and self.host_update.runtime.connectionState == 'disconnected':
            reconnect = True

        # Check parent type
        parent_type = self.get_parent_type(self.host_update)

        if self.folder_name:
            if self.module.check_mode:
                if reconnect or self.state == 'add_or_reconnect' or self.state == 'reconnect':
                    result = "Host would be reconnected and moved to folder '%s'" % self.folder_name
                else:
                    result = "Host would be moved to folder '%s'" % self.folder_name
            else:
                # Reconnect the host if disconnected or if specified by state
                if reconnect or self.state == 'add_or_reconnect' or self.state == 'reconnect':
                    self.reconnect_host(self.host_update)
                try:
                    try:
                        if parent_type == 'folder':
                            # Move ESXi host from folder to folder
                            task = self.folder.MoveIntoFolder_Task([self.host_update.parent])
                        elif parent_type == 'cluster':
                            self.put_host_in_maintenance_mode(self.host_update)
                            # Move ESXi host from cluster to folder
                            task = self.folder.MoveIntoFolder_Task([self.host_update])
                    except vim.fault.DuplicateName as duplicate_name:
                        self.module.fail_json(
                            msg="The folder already contains an object with the specified name : %s" %
                            to_native(duplicate_name)
                        )
                    except vim.fault.InvalidFolder as invalid_folder:
                        self.module.fail_json(
                            msg="The parent of this folder is in the list of objects : %s" %
                            to_native(invalid_folder)
                        )
                    except vim.fault.InvalidState as invalid_state:
                        self.module.fail_json(
                            msg="Failed to move host, this can be due to either of following :"
                            " 1. The host is not part of the same datacenter, 2. The host is not in maintenance mode : %s" %
                            to_native(invalid_state)
                        )
                    except vmodl.fault.NotSupported as not_supported:
                        self.module.fail_json(
                            msg="The target folder is not a host folder : %s" %
                            to_native(not_supported)
                        )
                    except vim.fault.DisallowedOperationOnFailoverHost as failover_host:
                        self.module.fail_json(
                            msg="The host is configured as a failover host : %s" %
                            to_native(failover_host)
                        )
                    except vim.fault.VmAlreadyExistsInDatacenter as already_exists:
                        self.module.fail_json(
                            msg="The host's virtual machines are already registered to a host in "
                            "the destination datacenter : %s" % to_native(already_exists)
                        )
                    changed, result = wait_for_task(task)
                except TaskError as task_error_exception:
                    task_error = task_error_exception.args[0]
                    self.module.fail_json(
                        msg="Failed to move host %s to folder %s due to %s" %
                        (self.esxi_hostname, self.folder_name, to_native(task_error))
                    )
                if reconnect or self.state == 'add_or_reconnect' or self.state == 'reconnect':
                    result = "Host reconnected and moved to folder '%s'" % self.folder_name
                else:
                    result = "Host moved to folder '%s'" % self.folder_name
        elif self.cluster_name:
            if self.module.check_mode:
                result = "Host would be moved to cluster '%s'" % self.cluster_name
            else:
                if parent_type == 'cluster':
                    # Put host in maintenance mode if moved from another cluster
                    self.put_host_in_maintenance_mode(self.host_update)
                resource_pool = None
                try:
                    try:
                        task = self.cluster.MoveHostInto_Task(
                            host=self.host_update, resourcePool=resource_pool
                        )
                    except vim.fault.TooManyHosts as too_many_hosts:
                        self.module.fail_json(
                            msg="No additional hosts can be added to the cluster : %s" % to_native(too_many_hosts)
                        )
                    except vim.fault.InvalidState as invalid_state:
                        self.module.fail_json(
                            msg="The host is already part of a cluster and is not in maintenance mode : %s" %
                            to_native(invalid_state)
                        )
                    except vmodl.fault.InvalidArgument as invalid_argument:
                        self.module.fail_json(
                            msg="Failed to move host, this can be due to either of following :"
                            " 1. The host is is not a part of the same datacenter as the cluster,"
                            " 2. The source and destination clusters are the same : %s" %
                            to_native(invalid_argument)
                        )
                    changed, result = wait_for_task(task)
                except TaskError as task_error_exception:
                    task_error = task_error_exception.args[0]
                    self.module.fail_json(
                        msg="Failed to move host to cluster '%s' due to : %s" %
                        (self.cluster_name, to_native(task_error))
                    )
                if reconnect or self.state == 'add_or_reconnect' or self.state == 'reconnect':
                    result = "Host reconnected and moved to cluster '%s'" % self.cluster_name
                else:
                    result = "Host moved to cluster '%s'" % self.cluster_name

        self.module.exit_json(changed=changed, msg=str(result))


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter_name=dict(type='str', required=True, aliases=['datacenter']),
        cluster_name=dict(type='str', aliases=['cluster']),
        esxi_hostname=dict(type='str', required=True),
        esxi_username=dict(type='str'),
        esxi_password=dict(type='str', no_log=True),
        esxi_ssl_thumbprint=dict(type='str', default='', aliases=['ssl_thumbprint']),
        fetch_ssl_thumbprint=dict(type='bool', default=True),
        state=dict(default='present',
                   choices=['present', 'absent', 'add_or_reconnect', 'reconnect'],
                   type='str'),
        folder=dict(type='str', aliases=['folder_name']),
        add_connected=dict(type='bool', default=True),
        force_connection=dict(type='bool', default=True),
        reconnect_disconnected=dict(type='bool', default=True),
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

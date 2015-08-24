#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: vmware_host
short_description: Add/remove ESXi host to/from vCenter
description:
    - This module can be used to add/remove an ESXi host to/from vCenter
version_added: 2.0
author: "Joseph Callen (@jcpowermac), Russell Teague (@mtnbikenc)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    hostname:
        description:
            - The hostname or IP address of the vSphere vCenter API server
        required: True
    username:
        description:
            - The username of the vSphere vCenter
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of the vSphere vCenter
        required: True
        aliases: ['pass', 'pwd']
    datacenter_name:
        description:
            - Name of the datacenter to add the host
        required: True
    cluster_name:
        description:
            - Name of the cluster to add the host
        required: True
    esxi_hostname:
        description:
            - ESXi hostname to manage
        required: True
    esxi_username:
        description:
            - ESXi username
        required: True
    esxi_password:
        description:
            - ESXi password
        required: True
    state:
        description:
            - Add or remove the host
        default: 'present'
        choices:
            - 'present'
            - 'absent'
        required: False
'''

EXAMPLES = '''
Example from Ansible playbook

    - name: Add ESXi Host to VCSA
      local_action:
        module: vmware_host
        hostname: vcsa_host
        username: vcsa_user
        password: vcsa_pass
        datacenter_name: datacenter_name
        cluster_name: cluster_name
        esxi_hostname: esxi_hostname
        esxi_username: esxi_username
        esxi_password: esxi_password
        state: present
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def find_host_by_cluster_datacenter(module):
    datacenter_name = module.params['datacenter_name']
    cluster_name = module.params['cluster_name']
    content = module.params['content']
    esxi_hostname = module.params['esxi_hostname']

    dc = find_datacenter_by_name(content, datacenter_name)
    cluster = find_cluster_by_name_datacenter(dc, cluster_name)

    for host in cluster.host:
        if host.name == esxi_hostname:
            return host, cluster

    return None, cluster


def add_host_to_vcenter(module):
    cluster = module.params['cluster']

    host_connect_spec = vim.host.ConnectSpec()
    host_connect_spec.hostName = module.params['esxi_hostname']
    host_connect_spec.userName = module.params['esxi_username']
    host_connect_spec.password = module.params['esxi_password']
    host_connect_spec.force = True
    host_connect_spec.sslThumbprint = ""
    as_connected = True
    esxi_license = None
    resource_pool = None

    try:
        task = cluster.AddHost_Task(host_connect_spec, as_connected, resource_pool, esxi_license)
        success, result = wait_for_task(task)
        return success, result
    except TaskError as add_task_error:
        # This is almost certain to fail the first time.
        # In order to get the sslThumbprint we first connect
        # get the vim.fault.SSLVerifyFault then grab the sslThumbprint
        # from that object.
        #
        # args is a tuple, selecting the first tuple
        ssl_verify_fault = add_task_error.args[0]
        host_connect_spec.sslThumbprint = ssl_verify_fault.thumbprint

    task = cluster.AddHost_Task(host_connect_spec, as_connected, resource_pool, esxi_license)
    success, result = wait_for_task(task)
    return success, result


def state_exit_unchanged(module):
    module.exit_json(changed=False)


def state_remove_host(module):
    host = module.params['host']
    changed = True
    result = None
    if not module.check_mode:
        if not host.runtime.inMaintenanceMode:
            maintenance_mode_task = host.EnterMaintenanceMode_Task(300, True, None)
            changed, result = wait_for_task(maintenance_mode_task)

        if changed:
            task = host.Destroy_Task()
            changed, result = wait_for_task(task)
        else:
            raise Exception(result)
    module.exit_json(changed=changed, result=str(result))


def state_update_host(module):
    module.exit_json(changed=False, msg="Currently not implemented.")


def state_add_host(module):

    changed = True
    result = None

    if not module.check_mode:
        changed, result = add_host_to_vcenter(module)
    module.exit_json(changed=changed, result=str(result))


def check_host_state(module):

    content = connect_to_api(module)
    module.params['content'] = content

    host, cluster = find_host_by_cluster_datacenter(module)

    module.params['cluster'] = cluster
    if host is None:
        return 'absent'
    else:
        module.params['host'] = host
        return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(datacenter_name=dict(required=True, type='str'),
                              cluster_name=dict(required=True, type='str'),
                              esxi_hostname=dict(required=True, type='str'),
                              esxi_username=dict(required=True, type='str'),
                              esxi_password=dict(required=True, type='str', no_log=True),
                              state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    try:
        # Currently state_update_dvs is not implemented.
        host_states = {
            'absent': {
                'present': state_remove_host,
                'absent': state_exit_unchanged,
            },
            'present': {
                'present': state_exit_unchanged,
                'absent': state_add_host,
            }
        }

        host_states[module.params['state']][check_host_state(module)](module)

    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()

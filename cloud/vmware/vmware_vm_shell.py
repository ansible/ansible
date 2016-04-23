#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, 2016 Ritesh Khadgaray <khadgaray () gmail.com>
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
module: vmware_vm_shell
short_description: Execute a process in VM
description:
    - Start a program in a VM without the need for network connection
version_added: 2.1
author: "Ritesh Khadgaray (@ritzk)"
notes:
    - Tested on vSphere 5.5
    - Only the first match against vm_id is used, even if there are multiple matches
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter:
        description:
            - The datacenter hosting the VM
            - Will help speed up search
        required: False
        default: None
    cluster:
        description:
            - The cluster hosting the VM
            - Will help speed up search
        required: False
        default: None
    vm_id:
        description:
            - The identification for the VM
        required: True
    vm_id_type:
        description:
            - The identification tag for the VM
        default: vm_name
        choices:
            - 'uuid'
            - 'dns_name'
            - 'inventory_path'
            - 'vm_name'
        required: False
        default: None
    vm_username:
        description:
            - The user to connect to the VM.
        required: False
        default: None
    vm_password:
        description:
            - The password used to login to the VM.
        required: False
        default: None
    vm_shell:
        description:
            - The absolute path to the program to start. On Linux this is executed via bash.
        required: True
    vm_shell_args:
        description:
            - The argument to the program.
        required: False
        default: None
    vm_shell_env:
        description:
            - Comma seperated list of envirnoment variable, specified in the guest OS notation
        required: False
        default: None
    vm_shell_cwd:
        description:
            - The current working directory of the application from which it will be run
        required: False
        default: None
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
    - name: shell execution
      local_action:
        module: vmware_vm_shell
        hostname: myVSphere
        username: myUsername
        password: mySecret
        datacenter: myDatacenter
        vm_id: NameOfVM
        vm_username: root
        vm_password: superSecret
        vm_shell: /bin/echo
        vm_shell_args: " $var >> myFile "
        vm_shell_env:
          - "PATH=/bin"
          - "VAR=test"
        vm_shell_cwd: "/tmp"

'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

# https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/execute_program_in_vm.py
def execute_command(content, vm, vm_username, vm_password, program_path, args="", env=None, cwd=None):

    creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
    cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(arguments=args, envVariables=env, programPath=program_path, workingDirectory=cwd)
    cmdpid = content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=creds, spec=cmdspec)

    return cmdpid

def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(datacenter=dict(default=None, type='str'),
                              cluster=dict(default=None, type='str'),
                              vm_id=dict(required=True, type='str'),
                              vm_id_type=dict(default='vm_name', type='str', choices=['inventory_path', 'uuid', 'dns_name', 'vm_name']),
                              vm_username=dict(required=False, type='str'),
                              vm_password=dict(required=False, type='str', no_log=True),
                              vm_shell=dict(required=True, type='str'),
                              vm_shell_args=dict(default=" ", type='str'),
                              vm_shell_env=dict(default=None, type='list'),
                              vm_shell_cwd=dict(default=None, type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(changed=False, msg='pyvmomi is required for this module')

    datacenter_name = p['datacenter']
    cluster_name = p['cluster']

    try:
        p = module.params
        content = connect_to_api(module)

        datacenter = None
        if datacenter_name:
            datacenter = find_datacenter_by_name(content, datacenter_name)
            if not datacenter:
                module.fail_json(changed=False, msg="datacenter not found")

        cluster = None
        if cluster_name:
            cluster = find_cluster_by_name(content, cluster_name, datacenter)
            if not cluster:
                module.fail_json(changed=False, msg="cluster not found")

        vm = find_vm_by_id(content, p['vm_id'], p['vm_id_type'], datacenter, cluster)
        if not vm:
            module.fail_json(msg='VM not found')

        msg = execute_command(content, vm, p['vm_username'], p['vm_password'],
                              p['vm_shell'], p['vm_shell_args'], p['vm_shell_env'], p['vm_shell_cwd'])

        module.exit_json(changed=True, uuid=vm.summary.config.uuid, msg=msg)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(changed=False, msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(changed=False, msg=method_fault.msg)
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()


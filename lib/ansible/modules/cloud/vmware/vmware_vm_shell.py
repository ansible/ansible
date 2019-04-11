#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2015-16, Ritesh Khadgaray <khadgaray () gmail.com>
# Copyright: (c) 2018, Ansible Project
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
module: vmware_vm_shell
short_description: Run commands in a VMware guest operating system
description:
    - Module allows user to run common system administration commands in the guest operating system.
version_added: "2.1"
author:
  - Ritesh Khadgaray (@ritzk)
  - Abhijeet Kasurde (@Akasurde)
notes:
    - Tested on vSphere 5.5, 6.0 and 6.5.
    - Only the first match against vm_id is used, even if there are multiple matches.
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter:
      description:
      - The datacenter hosting the virtual machine.
      - If set, it will help to speed up virtual machine search.
    cluster:
      description:
      - The cluster hosting the virtual machine.
      - If set, it will help to speed up virtual machine search.
    folder:
      description:
      - Destination folder, absolute or relative path to find an existing guest or create the new guest.
      - The folder should include the datacenter. ESX's datacenter is ha-datacenter.
      - 'Examples:'
      - '   folder: /ha-datacenter/vm'
      - '   folder: ha-datacenter/vm'
      - '   folder: /datacenter1/vm'
      - '   folder: datacenter1/vm'
      - '   folder: /datacenter1/vm/folder1'
      - '   folder: datacenter1/vm/folder1'
      - '   folder: /folder1/datacenter1/vm'
      - '   folder: folder1/datacenter1/vm'
      - '   folder: /folder1/datacenter1/vm/folder2'
      version_added: "2.4"
    vm_id:
      description:
      - Name of the virtual machine to work with.
      required: True
    vm_id_type:
      description:
      - The VMware identification method by which the virtual machine will be identified.
      default: vm_name
      choices: ['uuid', 'instance_uuid', 'dns_name', 'inventory_path', 'vm_name']
    vm_username:
      description:
      - The user to login-in to the virtual machine.
      required: True
    vm_password:
      description:
      - The password used to login-in to the virtual machine.
      required: True
    vm_shell:
      description:
      - The absolute path to the program to start.
      - On Linux, shell is executed via bash.
      required: True
    vm_shell_args:
      description:
      - The argument to the program.
      - The characters which must be escaped to the shell also be escaped on the command line provided.
      default: " "
    vm_shell_env:
      description:
      - Comma separated list of environment variable, specified in the guest OS notation.
    vm_shell_cwd:
      description:
      - The current working directory of the application from which it will be run.
    wait_for_process:
      description:
      - If set to C(True), module will wait for process to complete in the given virtual machine.
      default: False
      type: bool
      version_added: 2.7
    timeout:
      description:
      - Timeout in seconds.
      - If set to positive integers, then C(wait_for_process) will honor this parameter and will exit after this timeout.
      default: 3600
      version_added: 2.7
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Run command inside a virtual machine
  vmware_vm_shell:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter }}"
    folder: "/{{datacenter}}/vm"
    vm_id: "{{ vm_name }}"
    vm_username: root
    vm_password: superSecret
    vm_shell: /bin/echo
    vm_shell_args: " $var >> myFile "
    vm_shell_env:
      - "PATH=/bin"
      - "VAR=test"
    vm_shell_cwd: "/tmp"
  delegate_to: localhost
  register: shell_command_output

- name: Run command inside a virtual machine with wait and timeout
  vmware_vm_shell:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter }}"
    folder: "/{{datacenter}}/vm"
    vm_id: NameOfVM
    vm_username: root
    vm_password: superSecret
    vm_shell: /bin/sleep
    vm_shell_args: 100
    wait_for_process: True
    timeout: 2000
  delegate_to: localhost
  register: shell_command_with_wait_timeout

- name: Change user password in the guest machine
  vmware_vm_shell:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter }}"
    folder: "/{{datacenter}}/vm"
    vm_id: "{{ vm_name }}"
    vm_username: sample
    vm_password: old_password
    vm_shell: "/bin/echo"
    vm_shell_args: "-e 'old_password\nnew_password\nnew_password' | passwd sample > /tmp/$$.txt 2>&1"
  delegate_to: localhost

- name: Change hostname of guest machine
  vmware_vm_shell:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter }}"
    folder: "/{{datacenter}}/vm"
    vm_id: "{{ vm_name }}"
    vm_username: testUser
    vm_password: SuperSecretPassword
    vm_shell: "/usr/bin/hostnamectl"
    vm_shell_args: "set-hostname new_hostname > /tmp/$$.txt 2>&1"
  delegate_to: localhost
'''

RETURN = r'''
results:
    description: metadata about the new process after completion with wait_for_process
    returned: on success
    type: dict
    sample:
      {
        "cmd_line": "\"/bin/sleep\" 1",
        "end_time": "2018-04-26T05:03:21+00:00",
        "exit_code": 0,
        "name": "sleep",
        "owner": "dev1",
        "start_time": "2018-04-26T05:03:19+00:00",
        "uuid": "564db1e2-a3ff-3b0e-8b77-49c25570bb66",
      }
'''

import time
try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, find_cluster_by_name,
                                         find_datacenter_by_name, find_vm_by_id,
                                         vmware_argument_spec)


class VMwareShellManager(PyVmomi):
    def __init__(self, module):
        super(VMwareShellManager, self).__init__(module)
        datacenter_name = module.params['datacenter']
        cluster_name = module.params['cluster']
        folder = module.params['folder']
        self.pm = self.content.guestOperationsManager.processManager
        self.timeout = self.params.get('timeout', 3600)
        self.wait_for_pid = self.params.get('wait_for_process', False)

        datacenter = None
        if datacenter_name:
            datacenter = find_datacenter_by_name(self.content, datacenter_name)
            if not datacenter:
                module.fail_json(changed=False, msg="Unable to find %(datacenter)s datacenter" % module.params)

        cluster = None
        if cluster_name:
            cluster = find_cluster_by_name(self.content, cluster_name, datacenter)
            if not cluster:
                module.fail_json(changed=False, msg="Unable to find %(cluster)s cluster" % module.params)

        if module.params['vm_id_type'] == 'inventory_path':
            vm = find_vm_by_id(self.content,
                               vm_id=module.params['vm_id'],
                               vm_id_type="inventory_path",
                               folder=folder)
        else:
            vm = find_vm_by_id(self.content,
                               vm_id=module.params['vm_id'],
                               vm_id_type=module.params['vm_id_type'],
                               datacenter=datacenter,
                               cluster=cluster)

        if not vm:
            module.fail_json(msg='Unable to find virtual machine.')

        tools_status = vm.guest.toolsStatus
        if tools_status in ['toolsNotInstalled', 'toolsNotRunning']:
            self.module.fail_json(msg="VMWareTools is not installed or is not running in the guest."
                                      " VMware Tools are necessary to run this module.")

        try:
            self.execute_command(vm, module.params)
        except vmodl.RuntimeFault as runtime_fault:
            module.fail_json(changed=False, msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            module.fail_json(changed=False, msg=to_native(method_fault.msg))
        except Exception as e:
            module.fail_json(changed=False, msg=to_native(e))

    def execute_command(self, vm, params):
        # https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/execute_program_in_vm.py
        vm_username = params['vm_username']
        vm_password = params['vm_password']
        program_path = params['vm_shell']
        args = params['vm_shell_args']
        env = params['vm_shell_env']
        cwd = params['vm_shell_cwd']

        credentials = vim.vm.guest.NamePasswordAuthentication(username=vm_username,
                                                              password=vm_password)
        cmd_spec = vim.vm.guest.ProcessManager.ProgramSpec(arguments=args,
                                                           envVariables=env,
                                                           programPath=program_path,
                                                           workingDirectory=cwd)

        res = self.pm.StartProgramInGuest(vm=vm, auth=credentials, spec=cmd_spec)
        if self.wait_for_pid:
            res_data = self.wait_for_process(vm, res, credentials)
            results = dict(uuid=vm.summary.config.uuid,
                           owner=res_data.owner,
                           start_time=res_data.startTime.isoformat(),
                           end_time=res_data.endTime.isoformat(),
                           exit_code=res_data.exitCode,
                           name=res_data.name,
                           cmd_line=res_data.cmdLine)

            if res_data.exitCode != 0:
                results['msg'] = "Failed to execute command"
                results['changed'] = False
                results['failed'] = True
                self.module.fail_json(**results)
            else:
                results['changed'] = True
                results['failed'] = False
                self.module.exit_json(**results)
        else:
            self.module.exit_json(changed=True, uuid=vm.summary.config.uuid, msg=res)

    def process_exists_in_guest(self, vm, pid, creds):
        res = self.pm.ListProcessesInGuest(vm, creds, pids=[pid])
        if not res:
            self.module.fail_json(
                changed=False, msg='ListProcessesInGuest: None (unexpected)')
        res = res[0]
        if res.exitCode is None:
            return True, None
        else:
            return False, res

    def wait_for_process(self, vm, pid, creds):
        start_time = time.time()
        while True:
            current_time = time.time()
            process_status, res_data = self.process_exists_in_guest(vm, pid, creds)
            if not process_status:
                return res_data
            elif current_time - start_time >= self.timeout:
                self.module.fail_json(
                    msg="Timeout waiting for process to complete.",
                    vm=vm._moId,
                    pid=pid,
                    start_time=start_time,
                    current_time=current_time,
                    timeout=self.timeout)
            else:
                time.sleep(5)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            datacenter=dict(type='str'),
            cluster=dict(type='str'),
            folder=dict(type='str'),
            vm_id=dict(type='str', required=True),
            vm_id_type=dict(default='vm_name', type='str',
                            choices=['inventory_path',
                                     'uuid',
                                     'instance_uuid',
                                     'dns_name',
                                     'vm_name']),
            vm_username=dict(type='str', required=True),
            vm_password=dict(type='str', no_log=True, required=True),
            vm_shell=dict(type='str', required=True),
            vm_shell_args=dict(default=" ", type='str'),
            vm_shell_env=dict(type='list'),
            vm_shell_cwd=dict(type='str'),
            wait_for_process=dict(type='bool', default=False),
            timeout=dict(type='int', default=3600),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_if=[
            ['vm_id_type', 'inventory_path', ['folder']]
        ],
    )

    vm_shell_mgr = VMwareShellManager(module)


if __name__ == '__main__':
    main()

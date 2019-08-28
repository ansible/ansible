#!/usr/bin/python
#  -*- coding: utf-8 -*-
#  Copyright: (c) 2019, Ansible Project
#  Copyright: (c) 2019, Diane Wang <dianew@vmware.com>
#  GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_guest_screenshot
short_description: Create a screenshot of the Virtual Machine console.
description:
    - This module is used to take screenshot of the given virtual machine when virtual machine is powered on.
    - All parameters and VMware object names are case sensitive.
version_added: '2.9'
author:
    - Diane Wang (@Tomorrow9) <dianew@vmware.com>
notes:
    - Tested on vSphere 6.5 and 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
     description:
     - Name of the virtual machine.
     - This is a required parameter, if parameter C(uuid) or C(moid) is not supplied.
     type: str
   uuid:
     description:
     - UUID of the instance to gather facts if known, this is VMware's unique identifier.
     - This is a required parameter, if parameter C(name) or C(moid) is not supplied.
     type: str
   moid:
     description:
     - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
     - This is required if C(name) or C(uuid) is not supplied.
     version_added: '2.9'
     type: str
   folder:
     description:
     - Destination folder, absolute or relative path to find an existing guest.
     - This is a required parameter, only if multiple VMs are found with same name.
     - The folder should include the datacenter. ESXi server's datacenter is ha-datacenter.
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
     type: str
   cluster:
     description:
     - The name of cluster where the virtual machine is running.
     - This is a required parameter, if C(esxi_hostname) is not set.
     - C(esxi_hostname) and C(cluster) are mutually exclusive parameters.
     type: str
   esxi_hostname:
     description:
     - The ESXi hostname where the virtual machine is running.
     - This is a required parameter, if C(cluster) is not set.
     - C(esxi_hostname) and C(cluster) are mutually exclusive parameters.
     type: str
   datacenter:
     description:
     - The datacenter name to which virtual machine belongs to.
     type: str
   local_path:
     description:
     - 'If C(local_path) is not set, the created screenshot file will be kept in the directory of the virtual machine
       on ESXi host. If C(local_path) is set to a valid path on local machine, then the screenshot file will be
       downloaded from ESXi host to the local directory.'
     - 'If not download screenshot file to local machine, you can open it through the returned file URL in screenshot
       facts manually.'
     type: path
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: take a screenshot of the virtual machine console
  vmware_guest_screenshot:
    validate_certs: no
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    folder: "{{ folder_name }}"
    name: "{{ vm_name }}"
    local_path: "/tmp/"
  delegate_to: localhost
  register: take_screenshot

- name: Take a screenshot of the virtual machine console using MoID
  vmware_guest_screenshot:
    validate_certs: no
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    folder: "{{ folder_name }}"
    moid: vm-42
    local_path: "/tmp/"
  delegate_to: localhost
  register: take_screenshot
'''

RETURN = """
screenshot_info:
    description: display the facts of captured virtual machine screenshot file
    returned: always
    type: dict
    sample: {
            "virtual_machine": "test_vm",
            "screenshot_file": "[datastore0] test_vm/test_vm-1.png",
            "task_start_time": "2019-05-25T10:35:04.215016Z",
            "task_complete_time": "2019-05-25T10:35:04.412622Z",
            "result": "success",
            "screenshot_file_url": "https://test_vcenter/folder/test_vm/test_vm-1.png?dcPath=test-dc&dsName=datastore0",
            "download_local_path": "/tmp/",
            "download_file_size": 2367,
    }
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode, quote
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task, get_parent_datacenter
import os


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.change_detected = False

    def generate_http_access_url(self, file_path):
        # e.g., file_path is like this format: [datastore0] test_vm/test_vm-1.png
        # from file_path generate URL
        url_path = None
        if not file_path:
            return url_path

        path = "/folder/%s" % quote(file_path.split()[1])
        params = dict(dsName=file_path.split()[0].strip('[]'))
        if not self.is_vcenter():
            datacenter = 'ha-datacenter'
        else:
            datacenter = get_parent_datacenter(self.current_vm_obj).name.replace('&', '%26')
        params['dcPath'] = datacenter
        url_path = "https://%s%s?%s" % (self.params['hostname'], path, urlencode(params))

        return url_path

    def download_screenshot_file(self, file_url, local_file_path, file_name):
        response = None
        download_size = 0
        # file is downloaded as local_file_name when specified, or use original file name
        if local_file_path.endswith('.png'):
            local_file_name = local_file_path.split('/')[-1]
            local_file_path = local_file_path.rsplit('/', 1)[0]
        else:
            local_file_name = file_name
        if not os.path.exists(local_file_path):
            try:
                os.makedirs(local_file_path)
            except OSError as err:
                self.module.fail_json(msg="Exception caught when create folder %s on local machine, with error %s"
                                          % (local_file_path, to_native(err)))
        local_file = os.path.join(local_file_path, local_file_name)
        with open(local_file, 'wb') as handle:
            try:
                response = open_url(file_url, url_username=self.params.get('username'),
                                    url_password=self.params.get('password'), validate_certs=False)
            except Exception as err:
                self.module.fail_json(msg="Download screenshot file from URL %s, failed due to %s" % (file_url, to_native(err)))
            if not response or response.getcode() >= 400:
                self.module.fail_json(msg="Download screenshot file from URL %s, failed with response %s, response code %s"
                                          % (file_url, response, response.getcode()))
            bytes_read = response.read(2 ** 20)
            while bytes_read:
                handle.write(bytes_read)
                handle.flush()
                os.fsync(handle.fileno())
                download_size += len(bytes_read)
                bytes_read = response.read(2 ** 20)

        return download_size

    def get_screenshot_facts(self, task_info, file_url, file_size):
        screenshot_facts = dict()
        if task_info is not None:
            screenshot_facts = dict(
                virtual_machine=task_info.entityName,
                screenshot_file=task_info.result,
                task_start_time=task_info.startTime,
                task_complete_time=task_info.completeTime,
                result=task_info.state,
                screenshot_file_url=file_url,
                download_local_path=self.params.get('local_path'),
                download_file_size=file_size,
            )

        return screenshot_facts

    def take_vm_screenshot(self):
        if self.current_vm_obj.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
            self.module.fail_json(msg="VM is %s, valid power state is poweredOn." % self.current_vm_obj.runtime.powerState)
        try:
            task = self.current_vm_obj.CreateScreenshot_Task()
            wait_for_task(task)
        except vim.fault.FileFault as e:
            self.module.fail_json(msg="Failed to create screenshot due to errors when creating or accessing one or more"
                                      " files needed for this operation, %s" % to_native(e.msg))
        except vim.fault.InvalidState as e:
            self.module.fail_json(msg="Failed to create screenshot due to VM is not ready to respond to such requests,"
                                      " %s" % to_native(e.msg))
        except vmodl.RuntimeFault as e:
            self.module.fail_json(msg="Failed to create screenshot due to runtime fault, %s," % to_native(e.msg))
        except vim.fault.TaskInProgress as e:
            self.module.fail_json(msg="Failed to create screenshot due to VM is busy, %s" % to_native(e.msg))

        if task.info.state == 'error':
            return {'changed': self.change_detected, 'failed': True, 'msg': task.info.error.msg}
        else:
            download_file_size = None
            self.change_detected = True
            file_url = self.generate_http_access_url(task.info.result)
            if self.params.get('local_path'):
                if file_url:
                    download_file_size = self.download_screenshot_file(file_url=file_url,
                                                                       local_file_path=self.params['local_path'],
                                                                       file_name=task.info.result.split('/')[-1])
            screenshot_facts = self.get_screenshot_facts(task.info, file_url, download_file_size)
            return {'changed': self.change_detected, 'failed': False, 'screenshot_info': screenshot_facts}


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str'),
        esxi_hostname=dict(type='str'),
        cluster=dict(type='str'),
        local_path=dict(type='path'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ]
    )
    pyv = PyVmomiHelper(module)
    vm = pyv.get_vm()
    if not vm:
        vm_id = (module.params.get('uuid') or module.params.get('name') or module.params.get('moid'))
        module.fail_json(msg='Unable to find the specified virtual machine : %s' % vm_id)

    result = pyv.take_vm_screenshot()
    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()

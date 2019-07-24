#!/usr/bin/python
#  -*- coding: utf-8 -*-
#  Copyright: (c) 2018, Ansible Project
#  Copyright: (c) 2018, Diane Wang <dianew@vmware.com>
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
module: vmware_guest_video
short_description: Modify video card configurations of specified virtual machine in given vCenter infrastructure
description:
    - This module is used to reconfigure video card settings of given virtual machine.
    - All parameters and VMware object names are case sensitive.
version_added: '2.8'
author:
    - Diane Wang (@Tomorrow9) <dianew@vmware.com>
notes:
    - Tested on vSphere 6.0, 6.5 and 6.7
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
   datacenter:
     default: ha-datacenter
     description:
     - The datacenter name to which virtual machine belongs to.
     - This parameter is case sensitive.
     type: str
   gather_video_facts:
     description:
     - If set to True, return settings of the video card, other attributes are ignored.
     - If set to False, will do reconfiguration and return video card settings.
     type: bool
     default: 'no'
   use_auto_detect:
     description:
     - 'If set to True, applies common video settings to the guest operating system, attributes C(display_number) and C(video_memory_mb) are ignored.'
     - 'If set to False, the number of display and the total video memory will be reconfigured using C(display_number) and C(video_memory_mb).'
     type: bool
   display_number:
     description:
     - The number of display. Valid value from 1 to 10. The maximum display number is 4 on vCenter 6.0, 6.5 web UI.
     type: int
   video_memory_mb:
     description:
     - 'Valid total MB of video memory range of virtual machine is from 1.172 MB to 256 MB on ESXi 6.7U1,
        from 1.172 MB to 128 MB on ESXi 6.7 and previous versions.'
     - For specific guest OS, supported minimum and maximum video memory are different, please be careful on setting this.
     type: float
   enable_3D:
     description:
     - Enable 3D for guest operating systems on which VMware supports 3D.
     type: bool
   renderer_3D:
     description:
     - 'If set to C(automatic), selects the appropriate option (software or hardware) for this virtual machine automatically.'
     - 'If set to C(software), uses normal CPU processing for 3D calculations.'
     - 'If set to C(hardware), requires graphics hardware (GPU) for faster 3D calculations.'
     choices: [ automatic, software, hardware ]
     type: str
   memory_3D_mb:
     description:
     - The value of 3D Memory must be power of 2 and valid value is from 32 MB to 2048 MB.
     type: int
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Change video card settings of virtual machine
  vmware_guest_video:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    name: test-vm
    gather_video_facts: false
    use_auto_detect: false
    display_number: 2
    video_memory_mb: 8.0
    enable_3D: true
    renderer_3D: automatic
    memory_3D_mb: 512
  delegate_to: localhost
  register: video_facts

- name: Change video card settings of virtual machine using MoID
  vmware_guest_video:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    moid: vm-42
    gather_video_facts: false
    use_auto_detect: false
    display_number: 2
    video_memory_mb: 8.0
    enable_3D: true
    renderer_3D: automatic
    memory_3D_mb: 512
  delegate_to: localhost
  register: video_facts
'''

RETURN = """
video_status:
    description: metadata about the virtual machine's video card after managing them
    returned: always
    type: dict
    sample: {
        "auto_detect": false,
        "display_number": 2,
        "enable_3D_support": true,
        "memory_3D": 524288,
        "renderer_3D": "automatic",
        "video_memory": 8192
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.change_detected = False
        self.config_spec = vim.vm.ConfigSpec()
        self.config_spec.deviceChange = []
        self.video_card_facts = None

    @staticmethod
    def is_power_of_2(num):
        return num != 0 and ((num & (num - 1)) == 0)

    def gather_video_card_facts(self, vm_obj):
        """
        Gather facts about VM's video card settings
        Args:
            vm_obj: Managed object of virtual machine
        Returns: Video Card device and a list of dict video card configuration
        """
        video_facts = dict()
        video_card = None
        for device in vm_obj.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualVideoCard):
                video_card = device
                video_facts = dict(
                    auto_detect=device.useAutoDetect,
                    display_number=device.numDisplays,
                    video_memory=device.videoRamSizeInKB,
                    enable_3D_support=device.enable3DSupport,
                    renderer_3D=device.use3dRenderer,
                    memory_3D=device.graphicsMemorySizeInKB,
                )
                break
        return video_card, video_facts

    def get_video_card_spec(self, vm_obj):
        """
        Get device changes of virtual machine
        Args:
            vm_obj: Managed object of virtual machine
        Returns: virtual device spec
        """
        video_card, video_card_facts = self.gather_video_card_facts(vm_obj)
        self.video_card_facts = video_card_facts
        if video_card is None:
            self.module.fail_json(msg='Not get video card device of specified virtual machine.')
        video_spec = vim.vm.device.VirtualDeviceSpec()
        video_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        video_spec.device = video_card
        auto_detect = False
        enabled_3d = False

        if self.params['gather_video_facts']:
            return None
        if self.params['use_auto_detect'] is not None:
            if video_card_facts['auto_detect'] and self.params['use_auto_detect']:
                auto_detect = True
            elif not video_card_facts['auto_detect'] and self.params['use_auto_detect']:
                video_spec.device.useAutoDetect = True
                self.change_detected = True
                auto_detect = True
            elif video_card_facts['auto_detect'] and not self.params['use_auto_detect']:
                video_spec.device.useAutoDetect = False
                self.change_detected = True
        else:
            if video_card_facts['auto_detect']:
                auto_detect = True
        # useAutoDetect set to False then display number and video memory config can be changed
        if not auto_detect:
            if self.params['display_number'] is not None:
                if self.params['display_number'] < 1:
                    self.module.fail_json(msg="display_number attribute valid value: 1-10.")
                if self.params['display_number'] != video_card_facts['display_number']:
                    video_spec.device.numDisplays = self.params['display_number']
                    self.change_detected = True

            if self.params['video_memory_mb'] is not None:
                if self.params['video_memory_mb'] < 1.172:
                    self.module.fail_json(msg="video_memory_mb attribute valid value: ESXi 6.7U1(1.172-256 MB),"
                                              "ESXi 6.7/6.5/6.0(1.172-128 MB).")
                if int(self.params['video_memory_mb'] * 1024) != video_card_facts['video_memory']:
                    video_spec.device.videoRamSizeInKB = int(self.params['video_memory_mb'] * 1024)
                    self.change_detected = True
        else:
            if self.params['display_number'] is not None or self.params['video_memory_mb'] is not None:
                self.module.fail_json(msg="display_number and video_memory_mb can not be changed if use_auto_detect is true.")
        # useAutoDetect value not control 3D config
        if self.params['enable_3D'] is not None:
            if self.params['enable_3D'] != video_card_facts['enable_3D_support']:
                video_spec.device.enable3DSupport = self.params['enable_3D']
                self.change_detected = True
                if self.params['enable_3D']:
                    enabled_3d = True
            else:
                if video_card_facts['enable_3D_support']:
                    enabled_3d = True
        else:
            if video_card_facts['enable_3D_support']:
                enabled_3d = True
        # 3D is enabled then 3D memory and renderer method can be set
        if enabled_3d:
            if self.params['renderer_3D'] is not None:
                renderer = self.params['renderer_3D'].lower()
                if renderer not in ['automatic', 'software', 'hardware']:
                    self.module.fail_json(msg="renderer_3D attribute valid value: automatic, software, hardware.")
                if renderer != video_card_facts['renderer_3D']:
                    video_spec.device.use3dRenderer = renderer
                    self.change_detected = True
            if self.params['memory_3D_mb'] is not None:
                memory_3d = self.params['memory_3D_mb']
                if not self.is_power_of_2(memory_3d):
                    self.module.fail_json(msg="memory_3D_mb attribute should be an integer value and power of 2(32-2048).")
                else:
                    if memory_3d < 32 or memory_3d > 2048:
                        self.module.fail_json(msg="memory_3D_mb attribute should be an integer value and power of 2(32-2048).")
                if memory_3d * 1024 != video_card_facts['memory_3D']:
                    video_spec.device.graphicsMemorySizeInKB = memory_3d * 1024
                    self.change_detected = True
        else:
            if self.params['renderer_3D'] is not None or self.params['memory_3D_mb'] is not None:
                self.module.fail_json(msg='3D renderer or 3D memory can not be configured if 3D is not enabled.')
        if not self.change_detected:
            return None
        return video_spec

    def reconfigure_vm_video(self, vm_obj):
        """
        Reconfigure video card settings of virtual machine
        Args:
            vm_obj: Managed object of virtual machine
        Returns: Reconfigure results
        """
        video_card_spec = self.get_video_card_spec(vm_obj)
        if video_card_spec is None:
            return {'changed': False, 'failed': False, 'instance': self.video_card_facts}
        self.config_spec.deviceChange.append(video_card_spec)
        try:
            task = vm_obj.ReconfigVM_Task(spec=self.config_spec)
            wait_for_task(task)
        except vim.fault.InvalidDeviceSpec as invalid_device_spec:
            self.module.fail_json(msg="Failed to configure video card on given virtual machine due to invalid"
                                      " device spec : %s" % (to_native(invalid_device_spec.msg)),
                                  details="Please check ESXi server logs for more details.")
        except vim.fault.RestrictedVersion as e:
            self.module.fail_json(msg="Failed to reconfigure virtual machine due to"
                                      " product versioning restrictions: %s" % to_native(e.msg))
        if task.info.state == 'error':
            return {'changed': self.change_detected, 'failed': True, 'msg': task.info.error.msg}
        video_card_facts = self.gather_video_card_facts(vm_obj)[1]
        return {'changed': self.change_detected, 'failed': False, 'instance': video_card_facts}


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str', default='ha-datacenter'),
        gather_video_facts=dict(type='bool', default=False),
        use_auto_detect=dict(type='bool'),
        display_number=dict(type='int'),
        video_memory_mb=dict(type='float'),
        enable_3D=dict(type='bool'),
        renderer_3D=dict(type='str', choices=['automatic', 'software', 'hardware']),
        memory_3D_mb=dict(type='int'),
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
        vm_id = module.params.get('uuid') or module.params.get('name') or module.params.get('moid')
        module.fail_json(msg='Unable to find the specified virtual machine : %s' % vm_id)

    vm_facts = pyv.gather_facts(vm)
    vm_power_state = vm_facts['hw_power_status'].lower()
    if vm_power_state != 'poweredoff':
        module.fail_json(msg='VM state should be poweredoff to reconfigure video card settings.')
    result = pyv.reconfigure_vm_video(vm_obj=vm)
    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()

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
     - This is a required parameter, if parameter C(uuid) is not supplied.
   uuid:
     description:
     - UUID of the instance to gather facts if known, this is VMware's unique identifier.
     - This is a required parameter, if parameter C(name) is not supplied.
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
   datacenter:
     default: ha-datacenter
     description:
     - The datacenter name to which virtual machine belongs to.
     - This parameter is case sensitive.
   video_card:
     description:
     - Dict of video card configurations.
     - 'Valid attributes are:'
     - ' - C(gather_video_facts) (boolean): If set to true, return settings of video card, other attributes are ignored.'
     - '   If set to false, will do reconfiguration not just gather video card facts.'
     - ' - C(use_auto_detect) (boolean): If set to true, applies common video settings to the guest operating system,'
     - '   below attributes C(display_number) and C(video_memory_mb) will not be set. If set to false, you can select the'
     - '   number of displays and the total video memory using C(display_number), C(video_memory_mb) attributes.'
     - ' - C(display_number) (integer): Set the number of displays. Valid value from 1 to 10. But the maximum display'
     - '   number is 4 on vCenter 6.0, 6.5 web UI.'
     - ' - C(video_memory_mb) (integer): Valid total video memory range of virtual machine is from 1.172 MB to 256 MB'
     - '   on ESXi 6.7, from 1.172 MB to 128 MB on ESXi 6.5 and 6.0. For specific guest OS, supported minimum and maximum'
     - '   video memory are different, please be careful on setting this.'
     - ' - C(enable_3D) (boolean): Enable 3D for guest operating systems on which VMware supports 3D.'
     - ' - C(renderer_3D) (string): Specify 3D renderer, Valid values are:'
     - '     - C(Automatic) Selects the appropriate option (software or hardware) for this virtual machine automatically.'
     - '     - C(Software) Uses normal CPU processing for 3D calculations.'
     - '     - C(Hardware) Requires graphics hardware (GPU) for faster 3D calculations.'
     - '     Default: C(Automatic) select software or hardware automatically.'
     - ' - C(memory_3D_mb) (integer): the value of 3D Memory must be power of 2 and from 32 MB to 2048 MB.'
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
    video_card:
      gather_video_facts: false
      use_auto_detect: false
      display_number: 2
      video_memory_mb: 8
      enable_3D: true
      renderer_3D: automatic
      memory_3D_mb: 512
  delegate_to: localhost
  register: video_facts
'''

RETURN = """
disk_status:
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

        if 'gather_video_facts' in self.params['video_card'] and isinstance(self.params['video_card']['gather_video_facts'], bool)\
                and self.params['video_card']['gather_video_facts']:
            return None
        if 'use_auto_detect' in self.params['video_card']:
            if video_card_facts['auto_detect'] and self.params['video_card']['use_auto_detect']:
                auto_detect = True
            elif not video_card_facts['auto_detect'] and self.params['video_card']['use_auto_detect']:
                video_spec.device.useAutoDetect = True
                self.change_detected = True
                auto_detect = True
            elif video_card_facts['auto_detect'] and not self.params['video_card']['use_auto_detect']:
                video_spec.device.useAutoDetect = False
                self.change_detected = True
        else:
            if video_card_facts['auto_detect']:
                auto_detect = True
        # useAutoDetect set to False then display number and video memory config can be changed
        if not auto_detect:
            if 'display_number' in self.params['video_card']:
                try:
                    display_num = int(self.params['video_card'].get('display_number'))
                except ValueError as e:
                    self.module.fail_json(msg="video_card.display_number attribute should be an integer value(1-10).")
                if display_num < 1:
                    self.module.fail_json(msg="video_card.display_number attribute valid value: 1-10.")
                if display_num != video_card_facts['display_number']:
                    video_spec.device.numDisplays = display_num
                    self.change_detected = True

            if 'video_memory_mb' in self.params['video_card']:
                video_mem = self.params['video_card'].get('video_memory_mb')
                if (isinstance(video_mem, int) and video_mem < 2) or (isinstance(video_mem, float) and video_mem < 1.172):
                    self.module.fail_json(msg="video_card.video_memory_mb attribute valid value: ESXi 6.7(1.172-256 MB),"
                                              "ESXi 6.5/6.0(1.17-128 MB).")
                if not isinstance(video_mem, int) and not isinstance(video_mem, float):
                    self.module.fail_json(msg="video_card.video_memory_mb attribute should be an integer or "
                                              "decimal value ESXi 6.7(1.172-256 MB), ESXi 6.5/6.0(1.17-128 MB).")
                if int(video_mem * 1024) != video_card_facts['video_memory']:
                    video_spec.device.videoRamSizeInKB = int(video_mem * 1024)
                    self.change_detected = True
        else:
            if 'display_number' in self.params['video_card'] or 'video_memory_mb' in self.params['video_card']:
                self.module.fail_json(msg="video_card.display_number and video_card.video_memory_mb can not be changed "
                                          "if video_card.use_auto_detect is true.")
        # useAutoDetect value not control 3D config
        if 'enable_3D' in self.params['video_card']:
            if not isinstance(self.params['video_card']['enable_3D'], bool):
                self.module.fail_json(msg='video_card.enable_3D attribute should be a boolean.')
            if self.params['video_card']['enable_3D'] != video_card_facts['enable_3D_support']:
                video_spec.device.enable3DSupport = self.params['video_card']['enable_3D']
                self.change_detected = True
                if self.params['video_card']['enable_3D']:
                    enabled_3d = True
            else:
                if video_card_facts['enable_3D_support']:
                    enabled_3d = True
        else:
            if video_card_facts['enable_3D_support']:
                enabled_3d = True
        # 3D is enabled then 3D memory and renderer method can be set
        if enabled_3d:
            if 'renderer_3D' in self.params['video_card']:
                renderer = self.params['video_card'].get('renderer_3D').lower()
                if renderer not in ['automatic', 'software', 'hardware']:
                    self.module.fail_json(msg="video_card.renderer_3D attribute valid value: automatic, software, hardware.")
                if renderer != video_card_facts['renderer_3D']:
                    video_spec.device.use3dRenderer = renderer
                    self.change_detected = True
            if 'memory_3D_mb' in self.params['video_card']:
                try:
                    memory_3d = int(self.params['video_card'].get('memory_3D_mb'))
                except ValueError as e:
                    self.module.fail_json(msg="video_card.memory_3D_mb attribute should be an integer value and power of 2(32-2048).")
                if not self.is_power_of_2(memory_3d):
                    self.module.fail_json(msg="video_card.memory_3D_mb attribute should be an integer value and power of 2(32-2048).")
                else:
                    if memory_3d < 32 or memory_3d > 2048:
                        self.module.fail_json(msg="video_card.memory_3D_mb attribute should be an integer value and power of 2(32-2048).")
                if memory_3d * 1024 != video_card_facts['memory_3D']:
                    video_spec.device.graphicsMemorySizeInKB = memory_3d * 1024
                    self.change_detected = True
        else:
            if 'renderer_3D' in self.params['video_card'] or 'memory_3D_mb' in self.params['video_card']:
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
        folder=dict(type='str'),
        datacenter=dict(type='str', default='ha-datacenter'),
        video_card=dict(type='dict', default={}),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[['name', 'uuid']])
    pyv = PyVmomiHelper(module)
    vm = pyv.get_vm()
    if not vm:
        module.fail_json(msg='Not find the specified virtual machine : %s' % (module.params.get('uuid') or module.params.get('name')))

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


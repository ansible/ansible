#!/usr/bin/python

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Radoslaw Kuschel - <radoslaw.kuschel@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: rsd_boot

short_description: Change node Boot properties

version_added: "2.10"

description:
    - rsd_boot module overrides node boot properties.
    - 'The node on which boot override action will be performed can
      be identified by one of the following: uuid, identity, or name.'

options:
    boot_target:
        description: |
          Boot target to be used at next boot instead of the
          normal boot device.
          'none': boot from normal boot device.
          'pxe': boot from PXE environment.
          'floppy': Boot from the floppy disk drive.
          'cd': Boot from CD/DVD disc.
          'usb': Boot from a USB device.
          'hdd': boot from a hard drive.
          'bios_setup': Boot from BIOS setup utility.
          'utilities': Boot manufacturer's utilities programs.
          'diags': Boot manufacturer's diagnostics programs.
          'uefi_shell': Boot to the UEFI shell.
          'uefi_target': Boot to the UEFI device.
          'sd_card': Boot from an SD card.
          'uefi_http': Boot from UEFI HTTP network location.
          'remote_drive': boot from remote drive.
        required: true
        type: str
        choices: ['none', 'pxe', 'floppy', 'cd', 'usb', 'hdd',
                  'bios_setup', 'utilities', 'diags', 'uefi_shell',
                  'uefi_target', 'sd_card', 'uefi_http', 'remote_drive']
    boot_enable:
        description: |
             Set state of the boot source override feature.
             'disable': The system will boot as normal.
             'once': System will boot once on the next boot cycle.
             'continuous': System will boot continuously from given
             boot source.
        required: true
        type: str
        choices: ['disable', 'once', 'continuous']
    boot_mode:
        description: |
            - Set BIOS boot mode
            - 'legacy': Node will boot in non-UEFI boot mode.
            - 'uefi': None will boot in UEFI boot mode.
        required: true
        type: str
        choices: ['legacy', 'uefi']
extends_documentation_fragment:
    - rsd
author:
    - Radoslaw Kuschel (@radoslawKuschel)
'''
EXAMPLES = '''
---
- name: Override Boot options to boot once from remote drive in legacy mode.
  rsd_boot:
    id:
      value: 1
    boot_target: remote_drive
    boot_enable: once
    boot_mode: legacy

- name: Override Boot options to boot once from PXE boot in UEFI mode.
  rsd_boot:
    id:
      value: 1
    boot_target: pxe
    boot_enable: once
    boot_mode: uefi

'''

RETURN = '''
node:
    description: Information regarding the node.
    returned: On success
    type: complex
    contains:
        id:
            description: Node ID.
        name:
            description: Node name.
        uuid:
            description: Node uuid.
        current:
            type: complex
            description: Current boot settings
            boot_target:
                description: Boot target.
            boot_enable:
                description: State of the boot target.
            boot_mode:
                description: BIOS boot mode.
        previous:
            type: complex
            description: Previous boot settings
            boot_target:
                description: Boot target.
            boot_enable:
                description: State of the boot target.
            boot_mode:
                description: BIOS boot mode.

    sample:
        "id": "1"
        "name": "node_01"
        "previous":
            "boot_enable": "Continuous"
            "boot_mode": "Legacy"
            "boot_target": "Hdd"
        "current":
            "boot_enable": "Once"
            "boot_mode": "Legacy"
            "boot_target": "Pxe"
        "uuid": "254bbb38-b98c-46a0-af5f-bef452854061"
'''

from ansible.module_utils.remote_management.rsd.rsd_common import RSD
try:
    import sushy
except ImportError:
    pass


class RsdNodeBoot(RSD):

    def __init__(self):
        argument_spec = dict(
            boot_target=dict(
                type='str',
                required=True,
                choices=['none', 'pxe', 'floppy', 'cd', 'usb', 'hdd',
                         'bios_setup', 'utilities', 'diags', 'uefi_shell',
                         'uefi_target', 'sd_card', 'uefi_http', 'remote_drive']
            ),

            boot_enable=dict(
                type='str',
                required=True,
                choices=['disable', 'once', 'continuous']
            ),

            boot_mode=dict(
                type='str',
                required=False,
                choices=['legacy', 'uefi']
            ),
        )

        super(RsdNodeBoot, self).__init__(argument_spec, False)

    def _params_mappings(self, param):
        mappings = {
            'none': 'None',
            'pxe': 'Pxe',
            'floppy': 'Floppy',
            'cd': 'Cd',
            'usb': 'Usb',
            'hdd': 'Hdd',
            'bios_setup': 'BiosSetup',
            'utilities': 'Utilities',
            'diags': 'Diags',
            'uefi_shell': 'UefiShell',
            'uefi_target': 'UefiTarget',
            'sd_card': 'SDCard',
            'uefi_http': 'UefiHttp',
            'remote_drive': 'RemoteDrive',
            'disable': 'Disable',
            'once': 'Once',
            'continuous': 'Continuous',
            'legacy': 'Legacy',
            'uefi': 'UEFI'
        }

        param_keys = ['boot_target', 'boot_enable', 'boot_mode']
        requested_val = dict()

        for key in param_keys:
            value = param[key]
            if value:
                requested_val[key] = mappings[value]

        return requested_val

    def _get_current_node_boot_options(self, node):
        node_boot_opt = node.boot
        current_boot_opt = {
            'boot_target': node_boot_opt.boot_source_override_target,
            'boot_enable': node_boot_opt.boot_source_override_enabled,
            'boot_mode': node_boot_opt.boot_source_override_mode
        }

        return current_boot_opt

    def _return_boot_result(self, node, current_opt, requested_opt,
                            boot_options_diff):
        result = dict()

        if 'boot_mode' not in requested_opt:
            requested_opt['boot_mode'] = current_opt['boot_mode']

        result = dict()
        result["id"] = node.identity
        result["name"] = node.name
        result["uuid"] = node.uuid
        result["current"] = requested_opt
        result["previous"] = current_opt

        self.module.exit_json(changed=boot_options_diff, node=result)

    def _check_boot_opt_diff(self, current_boot_opt, requested_boot_opt):

        for attr in requested_boot_opt:
            if current_boot_opt[attr] != requested_boot_opt[attr]:
                return True

        return False

    def _change_boot_options(self, param, node):
        requested_opt = self._params_mappings(param)
        current_boot_opt = self._get_current_node_boot_options(node)
        boot_opt_diff = self._check_boot_opt_diff(current_boot_opt,
                                                  requested_opt)

        if boot_opt_diff is True:
            try:
                if param['boot_mode'] is None:
                    node.set_node_boot_source(
                        requested_opt['boot_target'],
                        enabled=requested_opt['boot_enable'])
                else:
                    node.set_node_boot_source(
                        requested_opt['boot_target'],
                        enabled=requested_opt['boot_enable'],
                        mode=requested_opt['boot_mode'])
            except (sushy.exceptions.InvalidParameterValueError) as e:
                self.module.fail_json(msg="Invalid Parameter: "
                                      "{0}".format(str(e)))

        self._return_boot_result(node, current_boot_opt, requested_opt,
                                 boot_opt_diff)

    def run(self):
        params = self.module.params
        node = self._get_node()
        self._change_boot_options(params, node)


def main():
    boot = RsdNodeBoot()
    boot.run()


if __name__ == '__main__':
    main()

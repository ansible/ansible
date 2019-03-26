#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: kubevirt_preset

short_description: Manage KubeVirt virtual machine presets

description:
    - Use Openshift Python SDK to manage the state of KubeVirt virtual machine presets.

version_added: "2.8"

author: KubeVirt Team (@kubevirt)

options:
    state:
        description:
            - Create or delete virtual machine presets.
        default: "present"
        choices:
            - present
            - absent
        type: str
    name:
        description:
            - Name of the virtual machine preset.
        required: true
        type: str
    namespace:
        description:
            - Namespace where the virtual machine preset exists.
        required: true
        type: str
    selector:
        description:
            - "Selector is a label query over a set of virtual machine preset."
        type: dict

extends_documentation_fragment:
  - k8s_auth_options
  - kubevirt_vm_options
  - kubevirt_common_options

requirements:
  - python >= 2.7
  - openshift >= 0.8.2
'''

EXAMPLES = '''
- name: Create virtual machine preset 'vmi-preset-small'
  kubevirt_preset:
      state: present
      name: vmi-preset-small
      namespace: vms
      memory: 64M
      selector:
        matchLabels:
            kubevirt.io/vmPreset: vmi-preset-small

- name: Remove virtual machine preset 'vmi-preset-small'
  kubevirt_preset:
      state: absent
      name: vmi-preset-small
      namespace: vms
'''

RETURN = '''
kubevirt_preset:
  description:
    - The virtual machine preset managed by the user.
    - "This dictionary contains all values returned by the KubeVirt API all options
       are described here U(https://kubevirt.io/api-reference/master/definitions.html#_v1_virtualmachineinstancepreset)"
  returned: success
  type: complex
  contains: {}
'''

import copy
import traceback


from ansible.module_utils.k8s.common import AUTH_ARG_SPEC

from ansible.module_utils.kubevirt import (
    virtdict,
    KubeVirtRawModule,
    VM_COMMON_ARG_SPEC
)


KIND = 'VirtualMachineInstancePreset'
VMP_ARG_SPEC = {
    'selector': {'type': 'dict'},
}


class KubeVirtVMPreset(KubeVirtRawModule):

    @property
    def argspec(self):
        """ argspec property builder """
        argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
        argument_spec.update(VM_COMMON_ARG_SPEC)
        argument_spec.update(VMP_ARG_SPEC)
        return argument_spec

    def execute_module(self):
        # Parse parameters specific for this module:
        definition = virtdict()
        selector = self.params.get('selector')

        if selector:
            definition['spec']['selector'] = selector

        # FIXME: Devices must be set, but we don't yet support any
        # attributes there, remove when we do:
        definition['spec']['domain']['devices'] = dict()

        # Execute the CURD of VM:
        dummy, definition = self.construct_vm_definition(KIND, definition, definition)
        result_crud = self.execute_crud(KIND, definition)
        changed = result_crud['changed']
        result = result_crud.pop('result')

        # Return from the module:
        self.exit_json(**{
            'changed': changed,
            'kubevirt_preset': result,
            'result': result_crud,
        })


def main():
    module = KubeVirtVMPreset()
    try:
        module.execute_module()
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()

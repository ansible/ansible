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
module: kubevirt_rs

short_description: Manage KubeVirt virtual machine replica sets

description:
    - Use Openshift Python SDK to manage the state of KubeVirt virtual machine replica sets.

version_added: "2.8"

author: KubeVirt Team (@kubevirt)

options:
    state:
        description:
            - Create or delete virtual machine replica sets.
        default: "present"
        choices:
            - present
            - absent
        type: str
    name:
        description:
            - Name of the virtual machine replica set.
        required: true
        type: str
    namespace:
        description:
            - Namespace where the virtual machine replica set exists.
        required: true
        type: str
    selector:
        description:
            - "Selector is a label query over a set of virtual machine."
        required: true
        type: dict
    replicas:
        description:
            - Number of desired pods. This is a pointer to distinguish between explicit zero and not specified.
            - Replicas defaults to 1 if newly created replica set.
        type: int

extends_documentation_fragment:
  - k8s_auth_options
  - kubevirt_vm_options
  - kubevirt_common_options

requirements:
  - python >= 2.7
  - openshift >= 0.8.2
'''

EXAMPLES = '''
- name: Create virtual machine replica set 'myvmir'
  kubevirt_rs:
      state: present
      name: myvmir
      namespace: vms
      wait: true
      replicas: 3
      memory: 64M
      labels:
        myvmi: myvmi
      selector:
        matchLabels:
            myvmi: myvmi
      disks:
         - name: containerdisk
           volume:
             containerDisk:
               image: kubevirt/cirros-container-disk-demo:latest
               path: /custom-disk/cirros.img
           disk:
             bus: virtio

- name: Remove virtual machine replica set 'myvmir'
  kubevirt_rs:
      state: absent
      name: myvmir
      namespace: vms
      wait: true
'''

RETURN = '''
kubevirt_rs:
  description:
    - The virtual machine virtual machine replica set managed by the user.
    - "This dictionary contains all values returned by the KubeVirt API all options
       are described here U(https://kubevirt.io/api-reference/master/definitions.html#_v1_virtualmachineinstance)"
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
    VM_COMMON_ARG_SPEC,
)


KIND = 'VirtualMachineInstanceReplicaSet'
VMIR_ARG_SPEC = {
    'replicas': {'type': 'int'},
    'selector': {'type': 'dict'},
}


class KubeVirtVMIRS(KubeVirtRawModule):

    @property
    def argspec(self):
        """ argspec property builder """
        argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
        argument_spec.update(copy.deepcopy(VM_COMMON_ARG_SPEC))
        argument_spec.update(copy.deepcopy(VMIR_ARG_SPEC))
        return argument_spec

    def wait_for_replicas(self, replicas):
        """ Wait for ready_replicas to equal the requested number of replicas. """
        resource = self.find_supported_resource(KIND)
        return_obj = None

        for event in resource.watch(namespace=self.namespace, timeout=self.params.get('wait_timeout')):
            entity = event['object']
            if entity.metadata.name != self.name:
                continue
            status = entity.get('status', {})
            readyReplicas = status.get('readyReplicas', 0)
            if readyReplicas == replicas:
                return_obj = entity
                break

        if not return_obj:
            self.fail_json(msg="Error fetching the patched object. Try a higher wait_timeout value.")
        if replicas and return_obj.status.readyReplicas is None:
            self.fail_json(msg="Failed to fetch the number of ready replicas. Try a higher wait_timeout value.")
        if replicas and return_obj.status.readyReplicas != replicas:
            self.fail_json(msg="Number of ready replicas is {0}. Failed to reach {1} ready replicas within "
                               "the wait_timeout period.".format(return_obj.status.ready_replicas, replicas))
        return return_obj.to_dict()

    def execute_module(self):
        # Parse parameters specific for this module:
        definition = virtdict()
        selector = self.params.get('selector')
        replicas = self.params.get('replicas')

        if selector:
            definition['spec']['selector'] = selector

        if replicas is not None:
            definition['spec']['replicas'] = replicas

        # defaults for template
        defaults = {'disks': [], 'volumes': [], 'interfaces': [], 'networks': []}

        # Execute the CURD of VM:
        template = definition['spec']['template']
        dummy, definition = self.construct_vm_definition(KIND, definition, template, defaults)
        result_crud = self.execute_crud(KIND, definition)
        changed = result_crud['changed']
        result = result_crud.pop('result')

        # When creating a new VMIRS object without specifying `replicas`, assume it's '1' to make the
        # wait logic work correctly
        if changed and result_crud['method'] == 'create' and replicas is None:
            replicas = 1

        # Wait for the new number of ready replicas after a CRUD update
        # Note1: doesn't work correctly when reducing number of replicas due to how VMIRS works (as of kubevirt 1.5.0)
        # Note2: not the place to wait for the VMIs to get deleted when deleting the VMIRS object; that *might* be
        #        achievable in execute_crud(); keywords: orphanDependents, propagationPolicy, DeleteOptions
        if self.params.get('wait') and replicas is not None and self.params.get('state') == 'present':
            result = self.wait_for_replicas(replicas)

        # Return from the module:
        self.exit_json(**{
            'changed': changed,
            'kubevirt_rs': result,
            'result': result_crud,
        })


def main():
    module = KubeVirtVMIRS()
    try:
        module.execute_module()
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()

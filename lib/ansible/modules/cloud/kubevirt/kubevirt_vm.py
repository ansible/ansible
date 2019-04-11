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
module: kubevirt_vm

short_description: Manage KubeVirt virtual machine

description:
    - Use Openshift Python SDK to manage the state of KubeVirt virtual machines.

version_added: "2.8"

author: KubeVirt Team (@kubevirt)

options:
    state:
        description:
            - Set the virtual machine to either I(present), I(absent), I(running) or I(stopped).
            - "I(present) - Create or update a virtual machine. (And run it if it's ephemeral.)"
            - "I(absent) - Remove a virtual machine."
            - "I(running) - Create or update a virtual machine and run it."
            - "I(stopped) - Stop a virtual machine. (This deletes ephemeral VMs.)"
        default: "present"
        choices:
            - present
            - absent
            - running
            - stopped
        type: str
    name:
        description:
            - Name of the virtual machine.
        required: true
        type: str
    namespace:
        description:
            - Namespace where the virtual machine exists.
        required: true
        type: str
    ephemeral:
        description:
            - If (true) ephemeral vitual machine will be created. When destroyed it won't be accessible again.
            - Works only with C(state) I(present) and I(absent).
        type: bool
        default: false
    datavolumes:
        description:
            - "DataVolumes are a way to automate importing virtual machine disks onto pvcs during the virtual machine's
               launch flow. Without using a DataVolume, users have to prepare a pvc with a disk image before assigning
               it to a VM or VMI manifest. With a DataVolume, both the pvc creation and import is automated on behalf of the user."
        type: list
    template:
        description:
            - "Name of Template to be used in creation of a virtual machine."
        type: str
    template_parameters:
        description:
            - "New values of parameters from Template."
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
- name: Start virtual machine 'myvm'
  kubevirt_vm:
      state: running
      name: myvm
      namespace: vms

- name: Create virtual machine 'myvm' and start it
  kubevirt_vm:
      state: running
      name: myvm
      namespace: vms
      memory: 64Mi
      cpu_cores: 1
      bootloader: efi
      smbios_uuid: 5d307ca9-b3ef-428c-8861-06e72d69f223
      cpu_model: Conroe
      headless: true
      hugepage_size: 2Mi
      tablets:
        - bus: virtio
          name: tablet1
      cpu_limit: 3
      cpu_shares: 2
      disks:
        - name: containerdisk
          volume:
            containerDisk:
              image: kubevirt/cirros-container-disk-demo:latest
              path: /custom-disk/cirros.img
          disk:
            bus: virtio

- name: Create virtual machine 'myvm' with multus network interface
  kubevirt_vm:
      name: myvm
      namespace: vms
      memory: 512M
      interfaces:
        - name: default
          bridge: {}
          network:
            pod: {}
        - name: mynet
          bridge: {}
          network:
            multus:
              networkName: mynetconf

- name: Combine inline definition with Ansible parameters
  kubevirt_vm:
      # Kubernetes specification:
      definition:
        metadata:
          labels:
            app: galaxy
            service: web
            origin: vmware

      # Ansible parameters:
      state: running
      name: myvm
      namespace: vms
      memory: 64M
      disks:
        - name: containerdisk
          volume:
            containerDisk:
              image: kubevirt/cirros-container-disk-demo:latest
              path: /custom-disk/cirros.img
          disk:
            bus: virtio

- name: Start ephemeral virtual machine 'myvm' and wait to be running
  kubevirt_vm:
      ephemeral: true
      state: running
      wait: true
      wait_timeout: 180
      name: myvm
      namespace: vms
      memory: 64M
      labels:
        kubevirt.io/vm: myvm
      disks:
        - name: containerdisk
          volume:
            containerDisk:
              image: kubevirt/cirros-container-disk-demo:latest
              path: /custom-disk/cirros.img
          disk:
            bus: virtio

- name: Start fedora vm with cloud init
  kubevirt_vm:
      state: running
      wait: true
      name: myvm
      namespace: vms
      memory: 1024M
      cloud_init_nocloud:
        userData: |-
          #cloud-config
          password: fedora
          chpasswd: { expire: False }
      disks:
        - name: containerdisk
          volume:
            containerDisk:
              image: kubevirt/fedora-cloud-container-disk-demo:latest
              path: /disk/fedora.qcow2
          disk:
            bus: virtio

- name: Remove virtual machine 'myvm'
  kubevirt_vm:
      state: absent
      name: myvm
      namespace: vms
'''

RETURN = '''
kubevirt_vm:
  description:
      - The virtual machine dictionary specification returned by the API.
      - "This dictionary contains all values returned by the KubeVirt API all options
         are described here U(https://kubevirt.io/api-reference/master/definitions.html#_v1_virtualmachine)"
  returned: success
  type: complex
  contains: {}
'''


import copy
import traceback

from ansible.module_utils.k8s.common import AUTH_ARG_SPEC

from ansible.module_utils.k8s.common import AUTH_ARG_SPEC
from ansible.module_utils.kubevirt import (
    virtdict,
    KubeVirtRawModule,
    VM_COMMON_ARG_SPEC,
    VM_SPEC_DEF_ARG_SPEC
)

VM_ARG_SPEC = {
    'ephemeral': {'type': 'bool', 'default': False},
    'state': {
        'type': 'str',
        'choices': [
            'present', 'absent', 'running', 'stopped'
        ],
        'default': 'present'
    },
    'datavolumes': {'type': 'list'},
    'template': {'type': 'str'},
    'template_parameters': {'type': 'dict'},
}

# Which params (can) modify 'spec:' contents of a VM:
VM_SPEC_PARAMS = list(VM_SPEC_DEF_ARG_SPEC.keys()) + ['datavolumes', 'template', 'template_parameters']


class KubeVirtVM(KubeVirtRawModule):

    @property
    def argspec(self):
        """ argspec property builder """
        argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
        argument_spec.update(VM_COMMON_ARG_SPEC)
        argument_spec.update(VM_ARG_SPEC)
        return argument_spec

    @staticmethod
    def fix_serialization(obj):
        if obj and hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return obj

    def _wait_for_vmi_running(self):
        for event in self._kind_resource.watch(namespace=self.namespace, timeout=self.params.get('wait_timeout')):
            entity = event['object']
            if entity.metadata.name != self.name:
                continue
            status = entity.get('status', {})
            phase = status.get('phase', None)
            if phase == 'Running':
                return entity

        self.fail("Timeout occurred while waiting for virtual machine to start. Maybe try a higher wait_timeout value?")

    def _wait_for_vm_state(self, new_state):
        if new_state == 'running':
            want_created = want_ready = True
        else:
            want_created = want_ready = False

        for event in self._kind_resource.watch(namespace=self.namespace, timeout=self.params.get('wait_timeout')):
            entity = event['object']
            if entity.metadata.name != self.name:
                continue
            status = entity.get('status', {})
            created = status.get('created', False)
            ready = status.get('ready', False)
            if (created, ready) == (want_created, want_ready):
                return entity

        self.fail("Timeout occurred while waiting for virtual machine to achieve '{0}' state. "
                  "Maybe try a higher wait_timeout value?".format(new_state))

    def manage_vm_state(self, new_state, already_changed):
        new_running = True if new_state == 'running' else False
        changed = False
        k8s_obj = {}

        if not already_changed:
            k8s_obj = self.get_resource(self._kind_resource)
            if not k8s_obj:
                self.fail("VirtualMachine object disappeared during module operation, aborting.")
            if k8s_obj.spec.get('running', False) == new_running:
                return False, k8s_obj

            newdef = dict(metadata=dict(name=self.name, namespace=self.namespace), spec=dict(running=new_running))
            k8s_obj, err = self.patch_resource(self._kind_resource, newdef, k8s_obj,
                                               self.name, self.namespace, merge_type='merge')
            if err:
                self.fail_json(**err)
            else:
                changed = True

        if self.params.get('wait'):
            k8s_obj = self._wait_for_vm_state(new_state)

        return changed, k8s_obj

    def construct_definition(self, kind, our_state, ephemeral):
        definition = virtdict()
        processedtemplate = {}

        # Construct the API object definition:
        vm_template = self.params.get('template')
        if vm_template:
            # Find the template the VM should be created from:
            template_resource = self.client.resources.get(api_version='template.openshift.io/v1', kind='Template', name='templates')
            proccess_template = template_resource.get(name=vm_template, namespace=self.params.get('namespace'))

            # Set proper template values taken from module option 'template_parameters':
            for k, v in self.params.get('template_parameters', {}).items():
                for parameter in proccess_template.parameters:
                    if parameter.name == k:
                        parameter.value = v

            # Proccess the template:
            processedtemplates_res = self.client.resources.get(api_version='template.openshift.io/v1', kind='Template', name='processedtemplates')
            processedtemplate = processedtemplates_res.create(proccess_template.to_dict()).to_dict()['objects'][0]

        if not ephemeral:
            definition['spec']['running'] = our_state == 'running'
        template = definition if ephemeral else definition['spec']['template']
        template['metadata']['labels']['vm.cnv.io/name'] = self.params.get('name')
        dummy, definition = self.construct_vm_definition(kind, definition, template)
        definition = dict(self.merge_dicts(processedtemplate, definition))

        return definition

    def execute_module(self):
        # Parse parameters specific to this module:
        ephemeral = self.params.get('ephemeral')
        k8s_state = our_state = self.params.get('state')
        kind = 'VirtualMachineInstance' if ephemeral else 'VirtualMachine'
        _used_params = [name for name in self.params if self.params[name] is not None]
        # Is 'spec:' getting changed?
        vm_spec_change = True if set(VM_SPEC_PARAMS).intersection(_used_params) else False
        changed = False
        crud_executed = False
        method = ''

        # Underlying module_utils/k8s/* code knows only of state == present/absent; let's make sure not to confuse it
        if ephemeral:
            # Ephemerals don't actually support running/stopped; we treat those as aliases for present/absent instead
            if our_state == 'running':
                self.params['state'] = k8s_state = 'present'
            elif our_state == 'stopped':
                self.params['state'] = k8s_state = 'absent'
        else:
            if our_state != 'absent':
                self.params['state'] = k8s_state = 'present'

        self.client = self.get_api_client()
        self._kind_resource = self.find_supported_resource(kind)
        k8s_obj = self.get_resource(self._kind_resource)
        if not self.check_mode and not vm_spec_change and k8s_state != 'absent' and not k8s_obj:
            self.fail("It's impossible to create an empty VM or change state of a non-existent VM.")

        # Changes in VM's spec or any changes to VMIs warrant a full CRUD, the latter because
        # VMIs don't really have states to manage; they're either present or don't exist
        # Also check_mode always warrants a CRUD, as that'll produce a sane result
        if vm_spec_change or ephemeral or k8s_state == 'absent' or self.check_mode:
            definition = self.construct_definition(kind, our_state, ephemeral)
            result = self.execute_crud(kind, definition)
            changed = result['changed']
            k8s_obj = result['result']
            method = result['method']
            crud_executed = True

        if ephemeral and self.params.get('wait') and k8s_state == 'present' and not self.check_mode:
            # Waiting for k8s_state==absent is handled inside execute_crud()
            k8s_obj = self._wait_for_vmi_running()

        if not ephemeral and our_state in ['running', 'stopped'] and not self.check_mode:
            # State==present/absent doesn't involve any additional VMI state management and is fully
            # handled inside execute_crud() (including wait logic)
            patched, k8s_obj = self.manage_vm_state(our_state, crud_executed)
            changed = changed or patched
            if changed:
                method = method or 'patch'

        # Return from the module:
        self.exit_json(**{
            'changed': changed,
            'kubevirt_vm': self.fix_serialization(k8s_obj),
            'method': method
        })


def main():
    module = KubeVirtVM()
    try:
        module.execute_module()
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()

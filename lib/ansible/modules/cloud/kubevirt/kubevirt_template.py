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
module: kubevirt_template

short_description: Manage KubeVirt templates

description:
    - Use Openshift Python SDK to manage the state of KubeVirt templates.

version_added: "2.8"

author: KubeVirt Team (@kubevirt)

options:
    name:
        description:
            - Name of the Template object.
        required: true
        type: str
    namespace:
        description:
            - Namespace where the Template object exists.
        required: true
        type: str
    objects:
        description:
            - List of any valid API objects, such as a I(DeploymentConfig), I(Service), etc. The object
              will be created exactly as defined here, with any parameter values substituted in prior to creation.
              The definition of these objects can reference parameters defined earlier.
            - As part of the the list user can pass also I(VirtualMachine) kind. When passing I(VirtualMachine)
              user must use Ansible structure of the parameters not the Kubernetes API structure. For more information
              please take a look at M(kubevirt_vm) module and at EXAMPLES section, where you can see example.
        type: list
    merge_type:
        description:
            - Whether to override the default patch merge approach with a specific type. By default, the strategic
              merge will typically be used.
        type: list
        choices: [ json, merge, strategic-merge ]
    display_name:
        description:
            - "A brief, user-friendly name, which can be employed by user interfaces."
        type: str
    description:
        description:
            - A description of the template.
            - Include enough detail that the user will understand what is being deployed...
               and any caveats they need to know before deploying. It should also provide links to additional information,
               such as a README file."
        type: str
    long_description:
        description:
            - "Additional template description. This may be displayed by the service catalog, for example."
        type: str
    provider_display_name:
        description:
            - "The name of the person or organization providing the template."
        type: str
    documentation_url:
        description:
            - "A URL referencing further documentation for the template."
        type: str
    support_url:
        description:
            - "A URL where support can be obtained for the template."
        type: str
    editable:
        description:
            - "Extension for hinting at which elements should be considered editable.
               List of jsonpath selectors. The jsonpath root is the objects: element of the template."
            - This is parameter can be used only when kubevirt addon is installed on your openshift cluster.
        type: list
    default_disk:
        description:
            - "The goal of default disk is to define what kind of disk is supported by the OS mainly in
               terms of bus (ide, scsi, sata, virtio, ...)"
            - The C(default_disk) parameter define configuration overlay for disks that will be applied on top of disks
              during virtual machine creation to define global compatibility and/or performance defaults defined here.
            - This is parameter can be used only when kubevirt addon is installed on your openshift cluster.
        type: dict
    default_volume:
        description:
            - "The goal of default volume is to be able to configure mostly performance parameters like
               caches if those are exposed by the underlying volume implementation."
            - The C(default_volume) parameter define configuration overlay for volumes that will be applied on top of volumes
              during virtual machine creation to define global compatibility and/or performance defaults defined here.
            - This is parameter can be used only when kubevirt addon is installed on your openshift cluster.
        type: dict
    default_nic:
        description:
            - "The goal of default network is similar to I(default_disk) and should be used as a template
               to ensure OS compatibility and performance."
            - The C(default_nic) parameter define configuration overlay for nic that will be applied on top of nics
              during virtual machine creation to define global compatibility and/or performance defaults defined here.
            - This is parameter can be used only when kubevirt addon is installed on your openshift cluster.
        type: dict
    default_network:
        description:
            - "The goal of default network is similar to I(default_volume) and should be used as a template
               that specifies performance and connection parameters (L2 bridge for example)"
            - The C(default_network) parameter define configuration overlay for networks that will be applied on top of networks
              during virtual machine creation to define global compatibility and/or performance defaults defined here.
            - This is parameter can be used only when kubevirt addon is installed on your openshift cluster.
        type: dict
    icon_class:
        description:
            - "An icon to be displayed with your template in the web console. Choose from our existing logo
            icons when possible. You can also use icons from FontAwesome. Alternatively, provide icons through
            CSS customizations that can be added to an OpenShift Container Platform cluster that uses your template.
            You must specify an icon class that exists, or it will prevent falling back to the generic icon."
        type: str
    parameters:
        description:
            - "Parameters allow a value to be supplied by the user or generated when the template is instantiated.
            Then, that value is substituted wherever the parameter is referenced. References can be defined in any
            field in the objects list field. This is useful for generating random passwords or allowing the user to
            supply a host name or other user-specific value that is required to customize the template."
            - "More information can be found at: U(https://docs.openshift.com/container-platform/3.6/dev_guide/templates.html#writing-parameters)"
        type: list
    version:
        description:
            - Template structure version.
            - This is parameter can be used only when kubevirt addon is installed on your openshift cluster.
        type: str

extends_documentation_fragment:
  - k8s_auth_options
  - k8s_state_options

requirements:
  - python >= 2.7
  - openshift >= 0.8.2
'''

EXAMPLES = '''
- name: Create template 'mytemplate'
  kubevirt_template:
    state: present
    name: myvmtemplate
    namespace: templates
    display_name: Generic cirros template
    description: Basic cirros template
    long_description: Verbose description of cirros template
    provider_display_name: Just Be Cool, Inc.
    documentation_url: http://theverycoolcompany.com
    support_url: http://support.theverycoolcompany.com
    icon_class: icon-linux
    default_disk:
      disk:
        bus: virtio
    default_nic:
      model: virtio
    default_network:
      resource:
        resourceName: bridge.network.kubevirt.io/cnvmgmt
    default_volume:
      containerDisk:
        image: kubevirt/cirros-container-disk-demo:latest
    objects:
      - name: ${NAME}
        kind: VirtualMachine
        memory: ${MEMORY_SIZE}
        state: present
        namespace: vms
    parameters:
      - name: NAME
        description: VM name
        generate: expression
        from: 'vm-[A-Za-z0-9]{8}'
      - name: MEMORY_SIZE
        description: Memory size
        value: 1Gi

- name: Remove template 'myvmtemplate'
  kubevirt_template:
    state: absent
    name: myvmtemplate
    namespace: templates
'''

RETURN = '''
kubevirt_template:
  description:
    - The template dictionary specification returned by the API.
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
    API_GROUP,
    MAX_SUPPORTED_API_VERSION
)


TEMPLATE_ARG_SPEC = {
    'name': {'required': True},
    'namespace': {'required': True},
    'state': {
        'default': 'present',
        'choices': ['present', 'absent'],
    },
    'force': {
        'type': 'bool',
        'default': False,
    },
    'merge_type': {
        'type': 'list',
        'choices': ['json', 'merge', 'strategic-merge']
    },
    'objects': {
        'type': 'list',
    },
    'display_name': {
        'type': 'str',
    },
    'description': {
        'type': 'str',
    },
    'long_description': {
        'type': 'str',
    },
    'provider_display_name': {
        'type': 'str',
    },
    'documentation_url': {
        'type': 'str',
    },
    'support_url': {
        'type': 'str',
    },
    'icon_class': {
        'type': 'str',
    },
    'version': {
        'type': 'str',
    },
    'editable': {
        'type': 'list',
    },
    'default_disk': {
        'type': 'dict',
    },
    'default_volume': {
        'type': 'dict',
    },
    'default_network': {
        'type': 'dict',
    },
    'default_nic': {
        'type': 'dict',
    },
    'parameters': {
        'type': 'list',
    },
}


class KubeVirtVMTemplate(KubeVirtRawModule):

    @property
    def argspec(self):
        """ argspec property builder """
        argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
        argument_spec.update(TEMPLATE_ARG_SPEC)
        return argument_spec

    def execute_module(self):
        # Parse parameters specific for this module:
        definition = virtdict()

        # Execute the CRUD of VM template:
        kind = 'Template'
        template_api_version = 'template.openshift.io/v1'

        # Fill in template parameters:
        definition['parameters'] = self.params.get('parameters')

        # Fill in the default Label
        labels = definition['metadata']['labels']
        labels['template.cnv.io/type'] = 'vm'

        # Fill in Openshift/Kubevirt template annotations:
        annotations = definition['metadata']['annotations']
        if self.params.get('display_name'):
            annotations['openshift.io/display-name'] = self.params.get('display_name')
        if self.params.get('description'):
            annotations['description'] = self.params.get('description')
        if self.params.get('long_description'):
            annotations['openshift.io/long-description'] = self.params.get('long_description')
        if self.params.get('provider_display_name'):
            annotations['openshift.io/provider-display-name'] = self.params.get('provider_display_name')
        if self.params.get('documentation_url'):
            annotations['openshift.io/documentation-url'] = self.params.get('documentation_url')
        if self.params.get('support_url'):
            annotations['openshift.io/support-url'] = self.params.get('support_url')
        if self.params.get('icon_class'):
            annotations['iconClass'] = self.params.get('icon_class')
        if self.params.get('version'):
            annotations['template.cnv.io/version'] = self.params.get('version')

        # TODO: Make it more Ansiblish, so user don't have to specify API JSON path, but rather Ansible params:
        if self.params.get('editable'):
            annotations['template.cnv.io/editable'] = self.params.get('editable')

        # Set defaults annotations:
        if self.params.get('default_disk'):
            annotations['defaults.template.cnv.io/disk'] = self.params.get('default_disk').get('name')
        if self.params.get('default_volume'):
            annotations['defaults.template.cnv.io/volume'] = self.params.get('default_volume').get('name')
        if self.params.get('default_nic'):
            annotations['defaults.template.cnv.io/nic'] = self.params.get('default_nic').get('name')
        if self.params.get('default_network'):
            annotations['defaults.template.cnv.io/network'] = self.params.get('default_network').get('name')

        # Process objects:
        self.client = self.get_api_client()
        definition['objects'] = []
        objects = self.params.get('objects') or []
        for obj in objects:
            if obj['kind'] != 'VirtualMachine':
                definition['objects'].append(obj)
            else:
                vm_definition = virtdict()

                # Set VM defaults:
                if self.params.get('default_disk'):
                    vm_definition['spec']['template']['spec']['domain']['devices']['disks'] = [self.params.get('default_disk')]
                if self.params.get('default_volume'):
                    vm_definition['spec']['template']['spec']['volumes'] = [self.params.get('default_volume')]
                if self.params.get('default_nic'):
                    vm_definition['spec']['template']['spec']['domain']['devices']['interfaces'] = [self.params.get('default_nic')]
                if self.params.get('default_network'):
                    vm_definition['spec']['template']['spec']['networks'] = [self.params.get('default_network')]

                # Set kubevirt API version:
                vm_definition['apiVersion'] = '%s/%s' % (API_GROUP, MAX_SUPPORTED_API_VERSION)

                # Construct k8s vm API object:
                vm_template = vm_definition['spec']['template']
                dummy, vm_def = self.construct_vm_template_definition('VirtualMachine', vm_definition, vm_template, obj)

                definition['objects'].append(vm_def)

        # Create template:
        resource = self.client.resources.get(api_version=template_api_version, kind=kind, name='templates')
        definition = self.set_defaults(resource, definition)
        result = self.perform_action(resource, definition)

        # Return from the module:
        self.exit_json(**{
            'changed': result['changed'],
            'kubevirt_template': result.pop('result'),
            'result': result,
        })


def main():
    module = KubeVirtVMTemplate()
    try:
        module.execute_module()
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()

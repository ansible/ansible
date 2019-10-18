#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, KubeVirt Team <@kubevirt>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: k8s_service

short_description: Manage Services on Kubernetes

version_added: "2.8"

author: KubeVirt Team (@kubevirt)

description:
  - Use Openshift Python SDK to manage Services on Kubernetes

extends_documentation_fragment:
  - k8s_auth_options

options:
  resource_definition:
    description:
    - A partial YAML definition of the Service object being created/updated. Here you can define Kubernetes
      Service Resource parameters not covered by this module's parameters.
    - "NOTE: I(resource_definition) has lower priority than module parameters. If you try to define e.g.
      I(metadata.namespace) here, that value will be ignored and I(metadata) used instead."
    aliases:
    - definition
    - inline
    type: dict
  state:
    description:
    - Determines if an object should be created, patched, or deleted. When set to C(present), an object will be
      created, if it does not already exist. If set to C(absent), an existing object will be deleted. If set to
      C(present), an existing object will be patched, if its attributes differ from those specified using
      module options and I(resource_definition).
    default: present
    choices:
    - present
    - absent
  force:
    description:
    - If set to C(True), and I(state) is C(present), an existing object will be replaced.
    default: false
    type: bool
  merge_type:
    description:
    - Whether to override the default patch merge approach with a specific type. By default, the strategic
      merge will typically be used.
    - For example, Custom Resource Definitions typically aren't updatable by the usual strategic merge. You may
      want to use C(merge) if you see "strategic merge patch format is not supported"
    - See U(https://kubernetes.io/docs/tasks/run-application/update-api-object-kubectl-patch/#use-a-json-merge-patch-to-update-a-deployment)
    - Requires openshift >= 0.6.2
    - If more than one merge_type is given, the merge_types will be tried in order
    - If openshift >= 0.6.2, this defaults to C(['strategic-merge', 'merge']), which is ideal for using the same parameters
      on resource kinds that combine Custom Resources and built-in resources. For openshift < 0.6.2, the default
      is simply C(strategic-merge).
    choices:
    - json
    - merge
    - strategic-merge
    type: list
  name:
    description:
      - Use to specify a Service object name.
    required: true
    type: str
  namespace:
    description:
      - Use to specify a Service object namespace.
    required: true
    type: str
  type:
    description:
      - Specifies the type of Service to create.
      - See U(https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types)
    choices:
      - NodePort
      - ClusterIP
      - LoadBalancer
      - ExternalName
  ports:
    description:
      - A list of ports to expose.
      - U(https://kubernetes.io/docs/concepts/services-networking/service/#multi-port-services)
    type: list
  selector:
    description:
      - Label selectors identify objects this Service should apply to.
      - U(https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
    type: dict

requirements:
  - python >= 2.7
  - openshift >= 0.6.2
'''

EXAMPLES = '''
- name: Expose https port with ClusterIP
  k8s_service:
    state: present
    name: test-https
    namespace: default
    ports:
    - port: 443
      protocol: TCP
    selector:
      key: special

- name: Expose https port with ClusterIP using spec
  k8s_service:
    state: present
    name: test-https
    namespace: default
    inline:
      spec:
        ports:
        - port: 443
          protocol: TCP
        selector:
          key: special
'''

RETURN = '''
result:
  description:
  - The created, patched, or otherwise present Service object. Will be empty in the case of a deletion.
  returned: success
  type: complex
  contains:
     api_version:
       description: The versioned schema of this representation of an object.
       returned: success
       type: str
     kind:
       description: Always 'Service'.
       returned: success
       type: str
     metadata:
       description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
       returned: success
       type: complex
     spec:
       description: Specific attributes of the object. Will vary based on the I(api_version) and I(kind).
       returned: success
       type: complex
     status:
       description: Current status details for the object.
       returned: success
       type: complex
'''

import copy
import traceback

from collections import defaultdict

from ansible.module_utils.k8s.common import AUTH_ARG_SPEC, COMMON_ARG_SPEC
from ansible.module_utils.k8s.raw import KubernetesRawModule


SERVICE_ARG_SPEC = {
    'state': {
        'default': 'present',
        'choices': ['present', 'absent'],
    },
    'force': {
        'type': 'bool',
        'default': False,
    },
    'resource_definition': {
        'type': 'dict',
        'aliases': ['definition', 'inline']
    },
    'name': {'required': True},
    'namespace': {'required': True},
    'merge_type': {'type': 'list', 'choices': ['json', 'merge', 'strategic-merge']},
    'selector': {'type': 'dict'},
    'type': {
        'type': 'str',
        'choices': [
            'NodePort', 'ClusterIP', 'LoadBalancer', 'ExternalName'
        ],
    },
    'ports': {'type': 'list'},
}


class KubernetesService(KubernetesRawModule):
    def __init__(self, *args, **kwargs):
        super(KubernetesService, self).__init__(*args, k8s_kind='Service', **kwargs)

    @staticmethod
    def merge_dicts(x, y):
        for k in set(x.keys()).union(y.keys()):
            if k in x and k in y:
                if isinstance(x[k], dict) and isinstance(y[k], dict):
                    yield (k, dict(KubernetesService.merge_dicts(x[k], y[k])))
                else:
                    yield (k, y[k])
            elif k in x:
                yield (k, x[k])
            else:
                yield (k, y[k])

    @property
    def argspec(self):
        """ argspec property builder """
        argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
        argument_spec.update(SERVICE_ARG_SPEC)
        return argument_spec

    def execute_module(self):
        """ Module execution """
        self.client = self.get_api_client()

        api_version = 'v1'
        selector = self.params.get('selector')
        service_type = self.params.get('type')
        ports = self.params.get('ports')

        definition = defaultdict(defaultdict)

        definition['kind'] = 'Service'
        definition['apiVersion'] = api_version

        def_spec = definition['spec']
        def_spec['type'] = service_type
        def_spec['ports'] = ports
        def_spec['selector'] = selector

        def_meta = definition['metadata']
        def_meta['name'] = self.params.get('name')
        def_meta['namespace'] = self.params.get('namespace')

        # 'resource_definition:' has lower priority than module parameters
        definition = dict(self.merge_dicts(self.resource_definitions[0], definition))

        resource = self.find_resource('Service', api_version, fail=True)
        definition = self.set_defaults(resource, definition)
        result = self.perform_action(resource, definition)

        self.exit_json(**result)


def main():
    module = KubernetesService()
    try:
        module.execute_module()
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Will Thames <@willthames>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: k8s_facts

short_description: Describe Kubernetes (K8s) objects

version_added: "2.7"

author:
    - "Will Thames (@willthames)"

description:
  - Use the OpenShift Python client to perform read operations on K8s objects.
  - Access to the full range of K8s APIs.
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.

options:
  api_version:
    description:
    - Use to specify the API version. in conjunction with I(kind), I(name), and I(namespace) to identify a
      specific object.
    default: v1
    aliases:
    - api
    - version
  kind:
    description:
    - Use to specify an object model. Use in conjunction with I(api_version), I(name), and I(namespace) to identify a
      specific object.
    required: yes
  name:
    description:
    - Use to specify an object name.  Use in conjunction with I(api_version), I(kind) and I(namespace) to identify a
      specific object.
  namespace:
    description:
    - Use to specify an object namespace. Use in conjunction with I(api_version), I(kind), and I(name)
      to identify a specfic object.
  label_selectors:
    description: List of label selectors to use to filter results
  field_selectors:
    description: List of field selectors to use to filter results

extends_documentation_fragment:
  - k8s_auth_options

requirements:
  - "python >= 2.7"
  - "openshift >= 0.6"
  - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Get an existing Service object
  k8s_facts:
    api_version: v1
    kind: Service
    name: web
    namespace: testing
  register: web_service

- name: Get a list of all service objects
  k8s_facts:
    api_version: v1
    kind: Service
    namespace: testing
  register: service_list

- name: Get a list of all pods from any namespace
  k8s_facts:
    kind: Pod
  register: pod_list

- name: Search for all Pods labelled app=web
  k8s_facts:
    kind: Pod
    label_selectors:
      - app = web
      - tier in (dev, test)

- name: Search for all running pods
  k8s_facts:
    kind: Pod
    field_selectors:
      - status.phase = running
'''

RETURN = '''
items:
  description:
  - The object(s) that exists
  returned: success
  type: complex
  contains:
    api_version:
      description: The versioned schema of this representation of an object.
      returned: success
      type: str
    kind:
      description: Represents the REST resource this object represents.
      returned: success
      type: str
    metadata:
      description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
      returned: success
      type: dict
    spec:
      description: Specific attributes of the object. Will vary based on the I(api_version) and I(kind).
      returned: success
      type: dict
    status:
      description: Current status details for the object.
      returned: success
      type: dict
'''


from ansible.module_utils.k8s.common import KubernetesAnsibleModule, AUTH_ARG_SPEC
import copy


class KubernetesFactsModule(KubernetesAnsibleModule):

    def __init__(self, *args, **kwargs):
        KubernetesAnsibleModule.__init__(self, *args,
                                         supports_check_mode=True,
                                         **kwargs)

    def execute_module(self):
        self.client = self.get_api_client()

        self.exit_json(changed=False,
                       **self.kubernetes_facts(self.params['kind'],
                                               self.params['api_version'],
                                               self.params['name'],
                                               self.params['namespace'],
                                               self.params['label_selectors'],
                                               self.params['field_selectors']))

    @property
    def argspec(self):
        args = copy.deepcopy(AUTH_ARG_SPEC)
        args.update(
            dict(
                kind=dict(required=True),
                api_version=dict(default='v1', aliases=['api', 'version']),
                name=dict(),
                namespace=dict(),
                label_selectors=dict(type='list', default=[]),
                field_selectors=dict(type='list', default=[]),
            )
        )
        return args


def main():
    KubernetesFactsModule().execute_module()


if __name__ == '__main__':
    main()

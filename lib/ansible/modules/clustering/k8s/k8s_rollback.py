#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2020, Julien Huon <@julienhuon> Institut National de l'Audiovisuel
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: k8s_rollback

short_description: Rollback Kubernetes (K8S) Deployments and DaemonSets

version_added: "2.10"

author:
    - "Julien Huon (@julienhuon)"

description:
  - Use the OpenShift Python client to perform the Rollback
  - Authenticate using either a config file, certificates, password or token.
  - Similar to the kubectl rollout undo command

options:
  api_version:
    description:
    - Use to specify the API version. in conjunction with I(kind), I(name), and I(namespace) to identify a
      specific object.
    default: apps/v1
    aliases:
    - api
    - version
    type: str
  kind:
    description:
    - Use to specify an object model. Deployment and DaemonSets are the only objects supported at the moment.
      Use in conjunction with I(api_version), I(name), and I(namespace) to identify a specific object.
    required: yes
    type: str
  name:
    description:
    - Use to specify an object name.  Use in conjunction with I(api_version), I(kind) and I(namespace) to identify a
      specific object.
    type: str
  namespace:
    description:
    - Use to specify an object namespace. Use in conjunction with I(api_version), I(kind), and I(name)
      to identify a specific object.
    type: str
  label_selectors:
    description: List of label selectors to use to filter results
    type: list
    elements: str
  field_selectors:
    description: List of field selectors to use to filter results
    type: list
    elements: str

extends_documentation_fragment:
  - k8s_auth_options

requirements:
  - "python >= 2.7"
  - "openshift >= 0.6"
  - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Rollback a failed deployment
  k8s_rollback:
    api_version: apps/v1
    kind: Deployment
    name: web
    namespace: testing
'''

RETURN = '''
resources:
  description:
  - The rollbacked object.
  returned: success
  type: complex
  contains:
    api_version:
      description: The versioned schema of this representation of an object.
      returned: success
      type: str
    code:
      description: The HTTP Code of the response
      returned: success
      type: str
    kind:
      description: Status
      returned: success
      type: str
    metadata:
      description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
      returned: success
      type: dict
    status:
      description: Current status details for the object.
      returned: success
      type: dict
'''

from ansible.module_utils.k8s.common import KubernetesAnsibleModule, AUTH_ARG_SPEC
import copy


class KubernetesRollbackModule(KubernetesAnsibleModule):

    def __init__(self, *args, **kwargs):
        KubernetesAnsibleModule.__init__(self, *args,
                                         supports_check_mode=True,
                                         **kwargs)
        self.kind = self.params['kind']
        self.api_version = self.params['api_version']
        self.name = self.params['name']
        self.namespace = self.params['namespace']
        self.managed_resource = {}

        if self.kind == "DaemonSet":
            self.managed_resource['kind'] = "ControllerRevision"
            self.managed_resource['api_version'] = "apps/v1"
        elif self.kind == "Deployment":
            self.managed_resource['kind'] = "ReplicaSet"
            self.managed_resource['api_version'] = "apps/v1"
        else:
            self.fail(msg="Cannot perform rollback on resource of kind {0}"
                      .format(self.kind))

    def execute_module(self):
        results = []
        self.client = self.get_api_client()

        resources = self.kubernetes_facts(self.kind,
                                          self.api_version,
                                          self.name,
                                          self.namespace,
                                          self.params['label_selectors'],
                                          self.params['field_selectors'])

        for resource in resources['resources']:
            result = self.perform_action(resource)
            results.append(result)

        if len(results) == 1:
            self.exit_json(**results[0])

        self.exit_json(**{
            'changed': True,
            'result': {
                'results': results
            }
        })

    def perform_action(self, resource):
        if self.kind == "DaemonSet":
            current_revision = resource['metadata']['generation']
        elif self.kind == "Deployment":
            current_revision = resource['metadata']['annotations']['deployment.kubernetes.io/revision']

        managed_resources = self.kubernetes_facts(self.managed_resource['kind'],
                                                  self.managed_resource['api_version'],
                                                  '',
                                                  self.namespace,
                                                  resource['spec']
                                                  ['selector']
                                                  ['matchLabels'],
                                                  '')

        prev_managed_resource = get_previous_revision(managed_resources['resources'],
                                                      current_revision)

        if self.kind == "Deployment":
            del prev_managed_resource['spec']['template']['metadata']['labels']['pod-template-hash']

            resource_patch = [{
                "op": "replace",
                "path": "/spec/template",
                "value": prev_managed_resource['spec']['template']
            }, {
                "op": "replace",
                "path": "/metadata/annotations",
                "value": {
                    "deployment.kubernetes.io/revision": prev_managed_resource['metadata']['annotations']['deployment.kubernetes.io/revision']
                }
            }]

            api_target = 'deployments'
            content_type = 'application/json-patch+json'
        elif self.kind == "DaemonSet":
            resource_patch = prev_managed_resource["data"]

            api_target = 'daemonsets'
            content_type = 'application/strategic-merge-patch+json'

        rollback = self.client.request("PATCH",
                                       "/apis/{0}/namespaces/{1}/{2}/{3}"
                                       .format(self.api_version,
                                               self.namespace,
                                               api_target,
                                               self.name),
                                       body=resource_patch,
                                       content_type=content_type)

        result = {'changed': True, 'result': {}}
        result['method'] = 'patch'
        result['body'] = resource_patch
        result['result'] = rollback.to_dict()
        return result

    @property
    def argspec(self):
        args = copy.deepcopy(AUTH_ARG_SPEC)
        args.update(
            dict(
                kind=dict(required=True),
                api_version=dict(default='apps/v1', aliases=['api', 'version']),
                name=dict(),
                namespace=dict(),
                label_selectors=dict(type='list', default=[]),
                field_selectors=dict(type='list', default=[]),
            )
        )
        return args


def get_previous_revision(all_resources, current_revision):
    for resource in all_resources:
        if resource['kind'] == 'ReplicaSet':
            if int(resource['metadata']
                   ['annotations']
                   ['deployment.kubernetes.io/revision']) == int(current_revision) - 1:
                return resource
        elif resource['kind'] == 'ControllerRevision':
            if int(resource['metadata']
                   ['annotations']
                   ['deprecated.daemonset.template.generation']) == int(current_revision) - 1:
                return resource
    return None


def main():
    KubernetesRollbackModule().execute_module()


if __name__ == '__main__':
    main()

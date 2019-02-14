#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Fabian von Feilitzsch <@fabianvf>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: k8s_wait

short_description: Wait for Kubernetes resources to reach a desired state

version_added: "2.8"

author:
    - "Fabian von Feilitzsch (@fabianvf)"

description:
  - Use the OpenShift Python client to perform read operations on K8s objects.
  - Pass the object definition from a source file or inline. See examples for reading
    files and using Jinja templates or vault-encrypted files.
  - Access to the full range of K8s APIs.
  - Use the M(k8s) module to perform create, update, or delete resources
  - Use the M(k8s_facts) module to obtain a list of items about an object of type C(kind)
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.
  - Implemented for C(state=present) for C(Deployment), C(DaemonSet) and C(Pod), and for C(state=absent) for all resource kinds.
  - For resource kinds without an implementation, returns immediately unless C(condition) or C(field) is set.

extends_documentation_fragment:
  - k8s_state_options
  - k8s_name_options
  - k8s_auth_options

options:
  field:
    description:
    - Specifies a field, operator, and comparison value to wait for on the status field of a resource.
    - Comparison is processed as C(name) C(operator) C(value)
    - For example, to check that there are more than two replicas in a stateful set, C(name) would be replicas,
      C(operator) would be gt, and C(value) would be 2
    - This would be processed as status.replicas > 2
    suboptions:
      name:
        description:
        - The name of the status field.
        - For example, on a C(StatefulSet), the C(readyReplicas) and C(updatedReplicas) might be set in the status.
      operator:
        description:
        - The operator to use to compare the status field and the provided value.
        - gt, gte, lt and lte will only work on numerical values. eq and neq will work with all fields.
        choices:
        - eq
        - neq
        - gt
        - lt
        - gte
        - lte
        default: eq
      value:
        description:
        - The value to compare with the the status field. Can be any type.
  condition:
    description:
    - Specifies a custom condition on the status to wait for.
    suboptions:
      type:
        description:
        - The type of condition to wait for. For example, the C(Pod) resource will set the C(Ready) condition (among others)
        - Required if you are specifying a C(condition). If left empty, the C(condition) field will be ignored.
        - The possible types for a condition are specific to each resource type in Kubernetes. See the API documentation of the status field
          for a given resource to see possible choices.
      status:
        description:
        - The value of the status field in your desired condition.
        - For example, if a C(Deployment) is paused, the C(Progressing) C(type) will have the C(Unknown) status.
        choices:
        - True
        - False
        - Unknown
      reason:
        description:
        - The value of the reason field in your desired condition
        - For example, if a C(Deployment) is paused, The C(Progressing) C(type) will have the C(DeploymentPaused) reason.
        - The possible reasons in a condition are specific to each resource type in Kubernetes. See the API documentation of the status field
          for a given resource to see possible choices.
  timeout:
    description:
    - How long in seconds to wait for the resource to end up in the desired state.
    default: 120
  label_selectors:
    description: List of label selectors to use to filter resources
  field_selectors:
    description: List of field selectors to use to filter resources
requirements:
  - "python >= 2.7"
  - "openshift >= 0.6"
  - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Create a StatefulSet
  k8s:
    definition: '{{ lookup("template", "statefulset.yaml.j2") }}'

- name: Wait for 2 replicas to report as ready
  k8s_wait:
    definition: '{{ lookup("template", "statefulset.yaml.j2") }}'
    field:
      name: readyReplicas
      operator: gte
      value: 2

- name: Pause an existing Deployment
  k8s:
    definition:
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: test-deploy
        namespace: default
      spec:
        pause: True

- name: Verify the Deployment has reported the pause in its conditions
  k8s_wait:
    api_version: apps/v1
    kind: Deployment
    namespace: default
    name: test-deploy
    condition:
      type: Progressing
      status: Unknown
      reason: DeploymentPaused
    timeout: 30

- name: Wait for all pods labeled app=web to report ready
  k8s_wait:
    kind: Pod
    label_selectors:
    - app=web
    condition:
      type: ContainersReady
      status: True
'''

RETURN = '''
result:
  description:
  - The object(s) being examined
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
       type: complex
     spec:
       description: Specific attributes of the object. Will vary based on the I(api_version) and I(kind).
       returned: success
       type: complex
     status:
       description: Current status details for the object.
       returned: success
       type: complex
     items:
       description: Returned only when multiple yaml documents are passed to src or resource_definition
       returned: when resource_definition or src contains list of objects
       type: list
duration:
  description:
  - elapsed time of task in seconds
  returned: success
  type: int
  sample: 48
'''

from ansible.module_utils.k8s.wait import KubernetesWaitModule


def main():
    KubernetesWaitModule().execute_module()


if __name__ == '__main__':
    main()

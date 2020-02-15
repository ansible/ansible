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

from ansible.module_utils.k8s.rollback import KubernetesAnsibleRollbackModule


def main():
    KubernetesAnsibleRollbackModule().execute_module()


if __name__ == '__main__':
    main()

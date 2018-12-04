#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Chris Houseknecht <@chouseknecht>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: k8s_scale

short_description: Set a new size for a Deployment, ReplicaSet, Replication Controller, or Job.

version_added: "2.5"

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Fabian von Feilitzsch (@fabianvf)"

description:
  - Similar to the kubectl scale command. Use to set the number of replicas for a Deployment, ReplicatSet,
    or Replication Controller, or the parallelism attribute of a Job. Supports check mode.

extends_documentation_fragment:
  - k8s_name_options
  - k8s_auth_options
  - k8s_resource_options
  - k8s_scale_options

requirements:
    - "python >= 2.7"
    - "openshift >= 0.6"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Scale deployment up, and extend timeout
  k8s_scale:
    api_version: v1
    kind: Deployment
    name: elastic
    namespace: myproject
    replicas: 3
    wait_timeout: 60

- name: Scale deployment down when current replicas match
  k8s_scale:
    api_version: v1
    kind: Deployment
    name: elastic
    namespace: myproject
    current_replicas: 3
    replicas: 2

- name: Increase job parallelism
  k8s_scale:
    api_version: batch/v1
    kind: job
    name: pi-with-timeout
    namespace: testing
    replicas: 2

# Match object using local file or inline definition

- name: Scale deployment based on a file from the local filesystem
  k8s_scale:
    src: /myproject/elastic_deployment.yml
    replicas: 3
    wait: no

- name: Scale deployment based on a template output
  k8s_scale:
    resource_definition: "{{ lookup('template', '/myproject/elastic_deployment.yml') | from_yaml }}"
    replicas: 3
    wait: no

- name: Scale deployment based on a file from the Ansible controller filesystem
  k8s_scale:
    resource_definition: "{{ lookup('file', '/myproject/elastic_deployment.yml') | from_yaml }}"
    replicas: 3
    wait: no
'''

RETURN = '''
result:
  description:
  - If a change was made, will return the patched object, otherwise returns the existing object.
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
'''

from ansible.module_utils.k8s.scale import KubernetesAnsibleScaleModule


def main():
    KubernetesAnsibleScaleModule().execute_module()


if __name__ == '__main__':
    main()

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

module: openshift

short_description: Manage OpenShift objects

version_added: "2.5"

author: "Chris Houseknecht (@chouseknecht)"

description:
  - Use the OpenShift Python client to perform CRUD operations on OpenShift objects.
  - Supports authentication using either a config file, certificates, password or token.

extends_documentation_fragment: kubernetes

requirements:
    - "python >= 2.7"
    - "openshift >= 0.3"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Create a project
  openshift:
    api_version: v1
    kind: Project
    name: testing
    description: Testing
    display_name: "This is a test project."
    state: present

- name: Create a Persistent Volume Claim from an inline definition
  openshift:
    state: present
    definition:
      apiVersion: v1
      kind: PersistentVolumeClaim
      metadata:
        name: elastic-volume
        namespace: testing
      spec:
        resources:
          requests:
            storage: 5Gi
        accessModes:
        - ReadWriteOnce

- name: Create a Deployment from an inline definition
  openshift:
    state: present
    definition:
      apiVersion: v1
      kind: DeploymentConfig
      metadata:
        name: elastic
        labels:
          app: galaxy
          service: elastic
        namespace: testing
      spec:
        template:
          metadata:
            labels:
              app: galaxy
              service: elastic
          spec:
            containers:
              - name: elastic
                volumeMounts:
                - mountPath: /usr/share/elasticsearch/data
                  name: elastic-volume
                command: ["elasticsearch"]
                image: "ansible/galaxy-elasticsearch:2.4.6"
            volumes:
              - name: elastic-volume
                persistentVolumeClaim:
                  claimName: elastic-volume
          replicas: 1
          strategy:
            type: Rolling

- name: Create a Deployment by reading the definition from a file
  openshift:
    state: present
    src: /testing/deployment.yml

- name: Get the list of all Deployments
  openshift:
    api_version: v1
    kind: DeploymentConfigList
    namespace: testing
  register: deployment_list

- name: Remove an existing Deployment
  openshift:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: testing
    state: absent

- name: Create a Secret
  openshift:
    inline:
      apiVersion: v1
      kind: Secret
      metadata:
        name: mysecret
        namespace: testing
      type: Opaque
      data:
        username: "{{ 'admin' | b64encode }}"
        password: "{{ 'foobard' | b64encode }}"

- name: Retrieve the Secret
  openshift:
    api: v1
    kind: Secret
    name: mysecret
    namespace: testing
  register: mysecret
'''

RETURN = '''
result:
  description:
  - The created, patched, or otherwise present object. Will be empty in the case of a deletion.
  returned: success
  type: dict
request:
  description:
  - The object sent to the API. Useful for troubleshooting unexpected differences and 404 errors.
  returned: when diff is true
  type: dict
diff:
  description:
  - List of differences found when determining if an existing object will be patched. A copy of the existing object
    is updated with the requested options, and the updated object is then compared to the original. If there are
    differences, they will appear here.
  returned: when diff is true
  type: list
'''

from ansible.module_utils.openshift_common import OpenShiftAnsibleModule


def main():
    OpenShiftAnsibleModule().execute_module()


if __name__ == '__main__':
    main()

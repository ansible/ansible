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

module: openshift_raw

short_description: Manage OpenShift objects

version_added: "2.5"

author: "Chris Houseknecht (@chouseknecht)"

description:
  - Use the OpenShift Python client to perform CRUD operations on OpenShift objects.
  - Pass the object definition from a source file or inline. See examples for reading
    files and using Jinja templates.
  - Access to the full range of K8s and OpenShift APIs.
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.

extends_documentation_fragment:
  - k8s_state_options
  - k8s_name_options
  - k8s_resource_options
  - k8s_auth_options

options:
  description:
    description:
    - Use only when creating a project, otherwise ignored. Adds a description to the project
      metadata.
  display_name:
    description:
    - Use only when creating a project, otherwise ignored. Adds a display name to the project
      metadata.

requirements:
    - "python >= 2.7"
    - "openshift == 0.4.3"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Create a project
  openshift_raw:
    api_version: v1
    kind: Project
    name: testing
    description: Testing
    display_name: "This is a test project."
    state: present

- name: Create a Persistent Volume Claim from an inline definition
  openshift_raw:
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
  openshift_raw:
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

- name: Remove an existing Deployment
  openshift_raw:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: testing
    state: absent

- name: Create a Secret
  openshift_raw:
    definition:
      apiVersion: v1
      kind: Secret
      metadata:
        name: mysecret
        namespace: testing
      type: Opaque
      data:
        username: "{{ 'admin' | b64encode }}"
        password: "{{ 'foobard' | b64encode }}"

- name: Retrieve a Secret
  openshift_raw:
    api: v1
    kind: Secret
    name: mysecret
    namespace: testing
  register: mysecret

# Passing the object definition from a file

- name: Create a Deployment by reading the definition from a local file
  openshift_raw:
    state: present
    src: /testing/deployment.yml

- name: Read definition file from the Ansible controller file system
  openshift_raw:
    state: present
    definition: "{{ lookup('file', '/testing/deployment.yml') | from_yaml }}"

- name: Read definition file from the Ansible controller file system after Jinja templating
  openshift_raw:
    state: present
    definition: "{{ lookup('template', '/testing/deployment.yml') | from_yaml }}"
'''

RETURN = '''
result:
  description:
  - The created, patched, or otherwise present object. Will be empty in the case of a deletion.
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
       description: Returned only when the I(kind) is a List type resource. Contains a set of objects.
       returned: when resource is a List
       type: list
'''

from ansible.module_utils.k8s.raw import OpenShiftRawModule


def main():
    OpenShiftRawModule().execute_module()


if __name__ == '__main__':
    main()

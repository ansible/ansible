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

extends_documentation_fragment:
  - kubernetes

requirements:
    - "python >= 2.7"
    - "openshift >= 0.3"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Create a project
  openshift:
    name: testing
    api_version: v1
    kind: namespace
    state: present

- name: Create a Service object from an inline definition
  openshift:
    state: present
    definition:
      apiVersion: v1
      kind: Service
      metadata:
        name: web
        namespace: testing
        labels:
          app: galaxy
          service: web
      spec:
        selector:
          app: galaxy
          service: web
        ports:
        - protocol: TCP
          targetPort: 8000
          name: port-8000-tcp
          port: 8000

- name: Create a Service object by reading the definition from a file
  openshift:
    state: present
    src: /testing/service.yml

- name: Remove an existing Service object
  openshift:
    state: absent
    api_version: v1
    kind: service
    namespace: testing
    name: web
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

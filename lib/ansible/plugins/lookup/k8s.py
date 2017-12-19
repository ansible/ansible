# -*- coding: utf-8 -*-
# (c) 2017, Kenneth D. Evensen <kevensen@redhat.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = """
    lookup: k8s
    
    version_added: "2.5"
    
    short_description: Returns the JSON definition of an object in Kubernetes
    
    description:
        - This lookup plugin provides the ability to query for information about objects. Uses the OpenShift
          Python client to enable authentication via config file, token, password, or certificates.
          
    options:
      kind:
        description:
          - The kind of OpenShift resource to read (e.g. Project, Service, Pod)
        required: True
      host:
        description:
          - The IP address of the host serving the OpenShift API
        required: False
        default: 127.0.0.1
      port:
        description:
          - The port on which to access the OpenShift API
        required: False
        default: 8443
      token:
        description:
          - The token to use for authentication against the OpenShift API.
          - This can be a user or ServiceAccount token.
        required: True
      validate_certs:
        description:
          - Whether or not to validate the TLS certificate of the API.
        required: False
        default: True
      namespace:
        description:
          - The namespace/project where the object resides.
        required: False
      resource_name:
        description:
          - The name of the object to query.
        required: False
      pretty:
        description:
          - Whether or not to prettify the output.  This is useful for debugging.
        required: False
        default: False
      labelSelector:
        description:
          - Additional labels to include in the query.
        required: False
      fieldSelector:
        description:
          - Specific fields on which to query.
        required: False
      resourceVersion:
        description:
          - Query for a specific resource version.
        required: False
"""

EXAMPLES = """
- name: Get Project {{ project_name }}
  set_fact:
    project_fact:  "{{ lookup('openshift',
                       kind='Project',
                       host=inventory_host,
                       token=hostvars[inventory_host]['ansible_sa_token'],
                       resource_name=project_name,
                       validate_certs=validate_certs) }}"
- name: Get All Service Accounts in a Project
  set_fact:
    service_fact: "{{ lookup('openshift',
                      kind='ServiceAccount',
                      host=inventory_host,
                      token=hostvars[inventory_host]['ansible_sa_token'],
                      namespace=project_name,
                      validate_certs=validate_certs) }}"
"""

RETURN = """
  _list:
    description:
      - An object definition or list of objects definitions returned from OpenShift.
    type: dict
"""


from ansible.plugins.lookup import LookupBase
from ansible.module_utils.k8s_lookup import KubernetesLookup


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        return KubernetesLookup().run(terms, variables=variables, **kwargs)

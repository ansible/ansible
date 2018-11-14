##
#  Copyright 2018 Red Hat | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = """
---
lookup: ansible tower
author: Sumit Jaiswal <sjaiswal@redhat.com>
version_added: "2.8"
short_description: Query Ansible Tower objects
description:
  - Uses the Ansible Tower RestAPI to fetch Ansible Tower specified objects.  This lookup
    supports adding additional keywords to filter the return data and specify
    the desired set of returned fields.
requirements:
  - ansible tower instance
extends_documentation_fragment: tower
options:
    _terms:
      description: The name of the object to return from Ansible Tower
      required: True
    filter:
      description: a dict object that is used to filter the return objects
"""

EXAMPLES = """
- name: fetch all ansible tower projects
  set_fact:
    list_projects: "{{ lookup('tower_lookup', 'projects', provider=tower_provider) }}"

- name: query ansible tower project
  set_fact:
    query_project: "{{ lookup('tower_lookup', 'projects', filter={'name':'test_project'}, provider=tower_provider) }}"

- name: fetch all ansible tower inventories
  set_fact:
    list_inventories: "{{ lookup('tower_lookup', 'inventories', provider=tower_provider) }}"

- name: query ansible tower inventories
  set_fact:
    query_inventorie: "{{ lookup('tower_lookup', 'inventories', filter={'name':'test_inventory'}, provider=tower_provider) }}"

- name: fetch all ansible tower job_templates
  set_fact:
    list_job_templates: "{{ lookup('tower_lookup', 'job_templates', provider=tower_provider) }}"

- name: query ansible tower job_templates
  set_fact:
    query_job_template: "{{ lookup('tower_lookup', 'job_templates', filter={'name':'test_job_template'}, provider=tower_provider) }}"

- name: fetch all ansible tower groups
  set_fact:
    list_groups: "{{ lookup('tower_lookup', 'groups', provider=tower_provider) }}"

- name: query ansible tower group
  set_fact:
    query_pgroup: "{{ lookup('tower_lookup', 'groups', filter={'name':'test_group'}, provider=tower_provider) }}"

- name: fetch all ansible tower users
  set_fact:
    list_users: "{{ lookup('tower_lookup', 'users', provider=tower_provider) }}"

- name: query ansible tower user
  set_fact:
    query_user: "{{ lookup('tower_lookup', 'users', filter={'username':'test_user'}, provider=tower_provider) }}"

- name: fetch all ansible tower credentials
  set_fact:
    list_credentials: "{{ lookup('tower_lookup', 'credentials', provider=tower_provider) }}"

- name: query ansible tower credential
  set_fact:
    query_credential: "{{ lookup('tower_lookup', 'credentials', filter={'name':'test_credential'}, provider=tower_provider) }}"

  vars:
    tower_provider:
      host: tower_01
      username: admin
      password: password
"""

RETURN = """
obj_type:
  description:
    - The object type specified in the terms argument
  returned: always
  type: complex
  contains:
    obj_field:
      - One or more obj_type fields as specified by return_fields argument or
        the default set of fields as per the object type
"""


from ansible.plugins.lookup import LookupBase
from ansible.module_utils.web_infrastructure.ansible_tower.api import client
from ansible.module_utils.web_infrastructure.ansible_tower.conf import settings
from ansible.module_utils._text import to_text
from ansible.errors import AnsibleError


class LookupModule(LookupBase):

    def run(self, terms, **kwargs):
        try:
            tower_module = terms[0]
        except IndexError:
            raise AnsibleError('missing argument in the lookup query')

        return_fields = kwargs.pop('return_fields', None)
        filter_data = kwargs.pop('filter', {})
        provider = kwargs.pop('provider', {})
        tower_auth = provider
        tower_module = '/' + tower_module + '/'

        with settings.runtime_values(**tower_auth):
            try:
                result = client.request('GET', tower_module, filter_data)
            except Exception as exc:
                raise AnsibleError(to_text(exc))

        return result.items()

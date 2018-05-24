#
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
lookup: nios
version_added: "2.5"
short_description: Query Infoblox NIOS objects
description:
  - Uses the Infoblox WAPI API to fetch NIOS specified objects.  This lookup
    supports adding additional keywords to filter the return data and specify
    the desired set of returned fields.
requirements:
  - infoblox_client
extends_documentation_fragment: nios
options:
    _terms:
      description: The name of the object to return from NIOS
      required: True
    return_fields:
      description: The list of field names to return for the specified object.
    filter:
      description: a dict object that is used to filter the return objects
    extattrs:
      description: a dict object that is used to filter on extattrs
"""

EXAMPLES = """
- name: fetch all networkview objects
  set_fact:
    networkviews: "{{ lookup('nios', 'networkview', provider={'host': 'nios01', 'username': 'admin', 'password': 'password'}) }}"

- name: fetch the default dns view
  set_fact:
    dns_views: "{{ lookup('nios', 'view', filter={'name': 'default'}, provider={'host': 'nios01', 'username': 'admin', 'password': 'password'}) }}"

# all of the examples below use credentials that are  set using env variables
# export INFOBLOX_HOST=nios01
# export INFOBLOX_USERNAME=admin
# export INFOBLOX_PASSWORD=admin

- name: fetch all host records and include extended attributes
  set_fact:
    host_records: "{{ lookup('nios', 'record:host', return_fields=['extattrs', 'name', 'view', 'comment']}) }}"


- name: use env variables to pass credentials
  set_fact:
    networkviews: "{{ lookup('nios', 'networkview') }}"

- name: get a host record
  set_fact:
    host: "{{ lookup('nios', 'record:host', filter={'name': 'hostname.ansible.com'}) }}"

- name: get the authoritative zone from a non default dns view
  set_fact:
    host: "{{ lookup('nios', 'zone_auth', filter={'fqdn': 'ansible.com', 'view': 'ansible-dns'}) }}"
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
from ansible.module_utils.net_tools.nios.api import WapiLookup
from ansible.module_utils.net_tools.nios.api import normalize_extattrs, flatten_extattrs
from ansible.errors import AnsibleError


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        try:
            obj_type = terms[0]
        except IndexError:
            raise AnsibleError('the object_type must be specified')

        return_fields = kwargs.pop('return_fields', None)
        filter_data = kwargs.pop('filter', {})
        extattrs = normalize_extattrs(kwargs.pop('extattrs', {}))
        provider = kwargs.pop('provider', {})
        wapi = WapiLookup(provider)
        res = wapi.get_object(obj_type, filter_data, return_fields=return_fields)
        if res is not None:
            for obj in res:
                if 'extattrs' in obj:
                    obj['extattrs'] = flatten_extattrs(obj['extattrs'])
        else:
            res = []
        return res

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
lookup: skydive
version_added: "2.8"
short_description: Query Skydive objects
description:
  - Uses the Skydive python REST client to return the queried object from
    Skydive network analyser.
requirements:
  - skydive-client
extends_documentation_fragment: skydive
options:
    filter:
      description: a dict object that is used to filter the return objects
"""

EXAMPLES = """
- name: return skydive metdata if present based on Name
  set_fact:
    skydive_meta: "{{ lookup('skydive_lookup', filter={'Name':'test-VirtualBox'}) }}"

- name: return skydive metdata if present based on TID
  set_fact:
    skydive: "{{ lookup('skydive_lookup', filter={'TID': '2b5e8263-89d3-5e01-506b-9120f49572b5'}, 
                                        provider={'host': 'nios01', 'username': 'admin', 'password': 'password'}) }}"
"""

RETURN = """
_list:
  description:
    - The list of queried object metadata
  returned: always
  type: list
"""


from ansible.plugins.lookup import LookupBase
from ansible.module_utils.network.skydive.api import skydive_lookup
from ansible.module_utils._text import to_text
from ansible.errors import AnsibleError


class LookupModule(LookupBase):

    def run(self, variables=None, **kwargs):

        provider = kwargs.pop('provider', {})
        filter_data = kwargs.pop('filter', {})
        try:
            skydive_obj = skydive_lookup(provider)
            result = skydive_obj.lookup_query(filter_data)
        except Exception as exc:
            raise AnsibleError(to_text(exc))

        return [result]

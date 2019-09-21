#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Richard Metzler
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


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = r'''
---
module: osquery_facts
version_added: "2.10"
short_description: get facts from osquery selects
requirements:
  - osqueryi
description:
  - execute osquery selects and return the values
options:
  name:
    description:
      - an identifier to namespace the return value under ansible_facts.osquery.<name>
    type: str
    required: true
  query:
    description:
      - The SELECT statement which is passed to osqueryi
    type: str
    required: true
author:
  - "Richard Metzler (@rmetzler)"
'''

EXAMPLES = r'''
- name: parse /etc/hosts
  osquery_facts:
    name: etc_hosts
    query: SELECT * FROM etc_hosts

- debug: var=osquery.etc_hosts
'''

RETURN = r'''
query:
    description: query as provided by the caller
    returned: success
    type: 'str'
    sample: SELECT * FROM etc_hosts
value:
    description: result as an array of dicts
    returned: success
    type: str
'''


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {'required': True},
            'query': {'required': True},
        },
        supports_check_mode=True,
    )

    name = module.params['name']
    query = module.params['query']
    command_options = [module.get_bin_path('osqueryi', True), query, '--json']
    command_result = module.run_command(command_options, check_rc=True)
    result = module.from_json(command_result[1])

    facts = dict()
    facts[name] = result
    args = {
        'changed': False,
        'ansible_facts': {'osquery': facts},
    }
    module.exit_json(**args)


if __name__ == '__main__':
    main()

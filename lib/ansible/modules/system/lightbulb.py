#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Ansible lightbulb module test commit
====================================
Nothing special here, just setting up the commit pipeline.

'''

# (c) 2017, Matthew Bach <mbach@redhat.com>
#
# This file is part of Ansible,
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'curated'}

DOCUMENTATION: = '''
---
module: ansible_lightbulb: Test module setup.
description:
    - None really
version_added: "2.3"
options:
  mode:
    description:
    - None here either

author: mbach
'''

EXAMPLES = '''
- name: make dummy module
  test:
  args:
    mode: none
'''

RETURN = '''
changes_needed:
  description: none here again
  type: dict
  returned: always
  sample: { "role": "add", "role grant": "add" }
  type: boolean
  returned: always
'''

# import module snippets
from ansible.module_utils.basic import AnsibleModule



def main():
    print("hello roflcopter")
    module = AnsibleModule(argument_spec={})
    response = {"hello": "world"}
    module.exit_json(changed=False, meta=response)


if __name__ == '__main__':
    main()

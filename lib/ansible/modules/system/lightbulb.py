#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, David Igou (digou@redhat.com)
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: lightbulb
description: This module does nothing then exits with msg="HELLO WORLD"
short_description: Says Hello World
version_added: "2.4"
author: "David Igou (@digou)"
'''

EXAMPLES = '''
- name: lightbulb module
  lightbulb:
'''

RETURN = '''
msg:
   description: simple Hello World message
   type: string
   returned: success
'''

from ansible.module_utils.basic import AnsibleModule

def main():
        global module
        module = AnsibleModule(
            argument_spec=dict(
                foo=dict(type='str', default='bar')
            )
        )
        module.exit_json(changed=False, msg="HELLO WORLD", foo=module.params['foo'])

if __name__ == '__main__':
        main()

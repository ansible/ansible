#!/usr/bin/python
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
                    'supported_by': 'community',
                    'status': ['preview', 'deprecated']}

DOCUMENTATION = '''
---
module: lightbulb
short_description: short descriptio
description: description
version_added: 2.4
author: nlove
options:
    foo:
        description: foo
        required: false
        default: bar
'''
EXAMPLES = '''
- name: light the world
  lightbulb:
    foo: bar
'''
RETURN = '''
changed:
    description: changed
    returned: when changed
    type: boolean
    sample: True
foo:
    description: foo
    returned: always
    type: string
    sample: bar
'''

from ansible.module_utils.basic import AnsibleModule
import logging
logging.basicConfig(filename='example.log', level=logging.DEBUG)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            foo=dict(required=False, default='bar')
        )
    )
    logging.debug(module.params['foo'])
    module.exit_json(changed=True, foo=module.params['foo'])


def add_things(add1, add2):
    return add1 + add2

if __name__ == '__main__':
    main()

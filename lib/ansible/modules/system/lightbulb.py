#!/usr/bin/python1
# -*- coding: utf-8 -*-

# (c) 2017, Derek Foster <derekfoster94@gmail.com>
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
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: lightbulb
author: "Derek Foster (@fostimus)"
version_added: "2.4"
short_description: "Hello World"
requirements: []
description:
    - Prints "hello world to msg"
notes:
    - For Windows targets, use the M(win_group) module instead.
'''

EXAMPLES = '''
# Example group command from Ansible Playbooks
- lightbulb:
'''

RETURN = '''
msg:
    description: Output of foo
    returned: hello world
    type: string
    sample: "hello world"
'''
from ansible.module_utils.basic import AnsibleModule
''' debugger and logging modules not on repo
import epdb
import q
'''


def add(num1, num2):
    if num1 is None:
        num1 = "NoneType"
    if num2 is None:
        num2 = "NoneType"
    return num1 + num2


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )
    res = {'foo': 'bar'}
    # q(res)
    # epdb.set_trace()
    module.exit_json(changed=True, msg=res)


if __name__ == '__main__':
    main()

#!/usr/bin/python
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
version_added: "2.3.1"
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

import epdb
import q

def main():
    module = AnsibleModule(
        argument_spec=dict()
    )
    foo = "hello world"
    q(foo)
    epdb.set_trace()
    module.exit_json(changed=True, msg=foo)

from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()

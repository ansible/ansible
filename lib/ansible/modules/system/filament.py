#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Roy Williams <roywilliams@redhat.com>
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
module: filament
version_added: "2.4"
short_description: This is a hello world module.
description:
    - This is a hello world module.
options:
  state:
    description:
      - Determines if hello world is present of not.
    default: present
author: Roy Williams (@chopskxw)
'''

EXAMPLES = '''
# Test we can logon to 'webservers' and print hello world.
# ansible webserver -m filament

# Example of an Ansible Playbook
- filament:

# Run avoiding change:
- filament:
    state: absent
'''

RETURN = '''
filament:
    description: prints hello world
    returned: success
    type: string
    sample: hello world
'''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            foo=dict(default='bar'),
        ),
        supports_check_mode=True
    )

    if module.params['state'] == 'absent':
        module.fail_json(msg="state set to absent")

    module.exit_json(changed=False, filament="hello world", foo="bar")


if __name__ == '__main__':
    main()

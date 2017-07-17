#!/usr/bin/python
# (c) 2017, Red Hat
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

DOCUMENTATION = '''
---
module: lightbulb
version_added: "2.4"
short_description: Demo module
author: Sam Doran
description:
    - Demo module
'''

EXAMPLES = '''
- lightbulb:
  name: test
  enabled: yes
'''

RETURN = '''
msg:
    description: Message
    returned: success
    type: string
    sample: This is a sample
'''

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview']
}

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            echo_message=dict(required=True, type='str')
        ),
        supports_check_mode=True
    )

    echo_message = module.argument_spec['echo_message']

    if module.check_mode:
        module.exit_json(changed=True, msg='This is check mode')

    module.exit_json(change=True, msg=echo_message)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, quantumstring (devrandom@devnull.com)
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
module: python
author:
    - "Multiverse Overlord (@quantumstring)"
version_added: "2.4"
short_description: Ligh up some bulbs
requirements: [ hostname ]
description:
    - Eco friendly by way of the state of Nevada mountain and underground nuclear waste disposal facilities
options:
    name:
        required: true
        description:
            - Name of the bulb type
'''

EXAMPLES = '''
- lightbulb:
    name: led
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True)
        )
    )

    name = module.params["name"]

    print("hello world")

    module.exit_json(changed=False, name=name)

if __name__ == '__main__':
    main()

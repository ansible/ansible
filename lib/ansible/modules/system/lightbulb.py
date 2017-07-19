#!/usr/bin/python
# -*- coding: utf-8 -*-

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
author:
    - "Ansible Core Team"
version_added: "2.4"
short_description:  Lightbulb.
description:
    - Lightbulb.
options:
  foo:
    description:
     - A foo string.
    required: false
    default: "hello world"
'''


EXAMPLES = '''
- name: lightbulb
  lightbulb:
      foo: hello world
'''


RETURN = '''
foo:
    description: lightbulb
    returned: success
    type: string
    sample: hello world
'''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            foo=dict(required=False, type='str'),
        ),
    )
    foo = module.params['foo'] or 'hello world'

    #import q
    #q(foo)

    #import pdb
    #pdb.set_trace()

    result = dict(
        foo=foo,
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()

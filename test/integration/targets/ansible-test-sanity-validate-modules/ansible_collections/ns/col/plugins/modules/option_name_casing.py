#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = '''
module: option_name_casing
short_description: Option names equal up to casing
description: Option names equal up to casing.
author:
  - Ansible Core Team
options:
  foo:
    description: Foo
    type: str
    aliases:
      - bar
      - FOO  # this one is ok
  Foo:
    description: Foo alias
    type: str
  Bar:
    description: Bar alias
    type: str
  bam:
    description: Bar alias 2
    aliases:
      - baR
    type: str
'''

EXAMPLES = '''#'''
RETURN = ''''''

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    module = AnsibleModule(argument_spec=dict(
        foo=dict(type='str', aliases=['bar', 'FOO']),
        Foo=dict(type='str'),
        Bar=dict(type='str'),
        bam=dict(type='str', aliases=['baR'])
    ))
    module.exit_json()

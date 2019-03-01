#!/usr/bin/python

# Copyright: (c) 2019, Jill Rouleau <jillr@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: filament
short_description: Developer filament module
version_added: "2.8"
description: "Foo"
options:
  name:
    description:
      - it's a name yo
    required: false
  foo:
    description:
      - bar
    required: false
author: "jillr (@jillr)"
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  filament:
    name:
      - hello world
    foo:
      - bar
'''

RETURN = '''
foo:
  description: foo
  type: str
  returned: bar
sum:
  description: sum
  type: int
  returned: seventeen
'''

from ansible.module_utils.basic import AnsibleModule


def add_some_stuff():
    _sum = 12 + 5
    return _sum


def run_module():
    module_args = dict(name=dict(type='str', required=False),
                       foo=dict(type='str', required=False, default='baz'),)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    result = {'foo': module_args['foo'], 'sum': add_some_stuff()}
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

#!/usr/bin/python

# Copyright: (c) 2019, Jason Neurohr <jason@jasonneurohr.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: randomstring

short_description: Generates a random string of the desired length with an optional prefix and/or suffix.

version_added: "2.10"

description:
    - A module to generate a random string of the desired length with an optional prefix and/or suffix.
    - Useful for situations where a random value is required to avoid clashes.

options:
    prefix:
        description:
            - A prefix to add to the output
        required: true
        type: str
    suffix:
        description:
            - A suffix to add to the output
        required: false
        type: str
    length:
        description:
            - The length of the output exclusive of the prefix and/or suffix
        required: false
        type: int
        default: 8

author:
    - Jason Neurohr (@jasonneurohr)
'''

EXAMPLES = '''
# No arguments
- name: Test with no arguments
  randomstring:
  register: random_string

# pass in a length
- name: Test with length
  randomstring:
    length: 10
  register: random_string

# pass in a prefix
- name: Test with prefix
  randomstring:
    prefix: beginning-
  register: random_string

# pass in a suffix
- name: Test with suffix
  randomstring:
    suffix: -end
  register: random_string

# pass in a prefix, suffix, and length
- name: Test with all options
  randomstring:
    prefix: beginning-
    suffix: -end
    length: 10
  register: random_string
'''

RETURN = '''
random_string:
    description: The generated random string
    type: str
    returned: always
total_length:
    description: The total length of the random string inclusive or prefix and/or suffix if provided
    type: str
    returned: always
'''

import random
import string

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        prefix=dict(type='str', required=False, default=None),
        suffix=dict(type='str', required=False, default=None),
        length=dict(type='int', required=False, default=8)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    output = generate_random_string(
        module.params['prefix'],
        module.params['suffix'],
        module.params['length']
    )

    result = dict(
        changed=False,
        random_string=output,
        total_length=len(output)
    )

    module.exit_json(**result)


def generate_random_string(prefix=None, suffix=None, length=8):
    """Generates a random string of letters and digits"""

    letters_and_digits = string.ascii_letters + string.digits

    output = ''.join(random.choice(letters_and_digits) for i in range(length))

    if prefix is not None:
        output = prefix + output

    if suffix is not None:
        output = output + suffix

    return output


def main():
    run_module()


if __name__ == '__main__':
    main()

#!/usr/bin/python

#
# Copyright (c) 2018 Red Hat, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

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

short_description: This is my sample module

version_added: "2.7"

description:
    - "This is my longer description explaining my sample module"

options:
    operator_a:
        description:
            - The 1st operator
        required: true
    operator_b:
        description:
            - The 2nd operator
        required: true

author:
    - Zhikang Zhang (@redhat.com)
'''

EXAMPLES = '''tbc'''

RETURN = '''
foo:
    description: return value for assert test
    returned: success
    type: string
    sample: bar
result:
    description: the result of addition calculation of input
    returned: success
    type: int
    sample: 2
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.filament_utils import str_to_int


def add(a, b):
    return a + b


def main():
    module_args = dict(
        operator_a=dict(required=True, type='int'),
        operator_b=dict(required=True, type='int'))
    result = dict(changed=False)
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    result["foo"] = "bar"
    result["msg"] = "type of the argument:{0}".format(type(module.params["operator_a"]))
    a = str_to_int(module.params["operator_a"])
    b = str_to_int(module.params["operator_b"])
    result["result"] = add(a, b)
    # pdb.set_trace()
    module.exit_json(**result)


if __name__ == "__main__":
    main()

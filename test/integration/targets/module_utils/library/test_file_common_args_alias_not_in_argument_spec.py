#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts import data

arg_spec = dict(
    foo=dict(type='str', aliases=['owner'])
)

module = AnsibleModule(argument_spec=arg_spec, add_file_common_args=True)
module.exit_json(argument_spec=module.argument_spec, params=module.params)

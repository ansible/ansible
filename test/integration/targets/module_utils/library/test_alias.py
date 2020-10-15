#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

arg_spec = dict(
    foo=dict(type='str', aliases=['baz'])
)

module = AnsibleModule(argument_spec=arg_spec)
module.exit_json(foo=module.params['foo'])

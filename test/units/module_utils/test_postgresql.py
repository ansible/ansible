import json

from ansible.compat.tests import unittest

from ansible.module_utils import postgres, basic
from ansible.module_utils.basic import AnsibleModule
from units.mock.procenv import swap_stdin_and_argv


import pprint


class TestPostgres(unittest.TestCase):
    def test(self):
        params = {'foo': 'blippy'}
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS=params))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            a_module = AnsibleModule(argument_spec={'foo': {'required': True, 'aliases': ['name']}})
            res = postgres.params_to_kwmap(a_module)
            pprint.pprint(res)


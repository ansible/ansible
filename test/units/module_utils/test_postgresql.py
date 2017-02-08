import json

from ansible.compat.tests import unittest

from ansible.module_utils import postgres
from ansible.module_utils.basic import AnsibleModule
from units.mock.procenv import swap_stdin_and_argv


import pprint


class TestPostgres(unittest.TestCase):
    def test(self):
        params = {'foo': 'blippy'}
        # module weirdness and testing shenagigans
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS=params))
        self.stdin_swap = swap_stdin_and_argv(stdin_data=args)
        self.stdin_swap.__enter__()

        a_module = AnsibleModule(argument_spec={'foo': {'required': True, 'aliases': ['name']}})
        res = postgres.params_to_kwmap(a_module)
        pprint.pprint(res)

        # unittest doesn't have a clean place to use a context manager, so we have to enter/exit manually
        self.stdin_swap.__exit__(None, None, None)

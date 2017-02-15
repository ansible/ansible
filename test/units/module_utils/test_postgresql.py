import json

from ansible.compat.tests import unittest

from ansible.module_utils import postgres, basic
from ansible.module_utils.basic import AnsibleModule
from units.mock.procenv import swap_stdin_and_argv


import pprint


class TestPostgres(unittest.TestCase):
    def test_ensure_libs_no_rootcert(self):
        params = {'foo': 'blippy'}
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS=params))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            error_txt = postgres.ensure_libs(sslrootcert=None)
            self.assertFalse(error_txt)
            pprint.pprint(error_txt)

    def test_ensure_libs_with_rootcert(self):
        params = {'foo': 'blippy'}
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS=params))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None

            error_txt = postgres.ensure_libs(sslrootcert=True)
            self.assertFalse(error_txt)
            pprint.pprint(error_txt)

#    def test_sslmode_prefer(self):
#        params = {'foo': 'blippy'}
#        args = json.dumps(dict(ANSIBLE_MODULE_ARGS=params))
#
#        with swap_stdin_and_argv(stdin_data=args):
#            basic._ANSIBLE_ARGS = None
#            error_txt = postgres.ensure_libs(sslrootcert=None)
#            self.assertFalse(error_txt)
#            #a_module = AnsibleModule(argument_spec={'foo': {'required': True, 'aliases': ['name']}})
#            #res = postgres.params_to_kwmap(a_module)
#            pprint.pprint(error_txt)

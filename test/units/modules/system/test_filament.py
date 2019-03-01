from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.modules.system import filament
from ansible.module_utils._text import to_bytes
from units.modules.utils import (AnsibleExitJson,
                                 AnsibleFailJson,
                                 ModuleTestCase,
                                 set_module_args,)
import json


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


def get_bin_path(self, arg, required=False):
    """Mock AnsibleModule.get_bin_path"""
    if arg.endswith('my_command'):
        return '/usr/bin/my_command'
    else:
        if required:
            fail_json(msg='%r not found !' % arg)


class TestFilament(ModuleTestCase):

    def setUp(self):
        super(TestFilament, self).setUp()
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json,
                                                 get_bin_path=get_bin_path)
        self.mock_module_helper.start()

    def test_add_some_stuff(self):
        set_module_args({'name': 'module_test'})
        result = filament.add_some_stuff()
        self.assertEquals(result, 17)

    def test_run_module_success_all_things(self):
        set_module_args({'name': 'module_test'})
        with self.assertRaises(AnsibleExitJson) as result:
            filament.main()
            expected = {'changed': False, 'foo': '!bar', 'sum': '17'}
            self.assertEqual(result, expected)
            self.assertIsInstance(result['foo'], str)
            self.assertIsInstance(result['sum'], int)

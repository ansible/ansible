import sys

from ansible.compat.tests.mock import patch, Mock
from ansible.compat.tests import unittest
from ansible.module_utils import basic
import json
from ansible.module_utils._text import to_bytes

base_modules_mock = Mock()
nitro_service_mock = Mock()
nitro_exception_mock = Mock()


base_modules_to_mock = {
    'nssrc': base_modules_mock,
    'nssrc.com': base_modules_mock,
    'nssrc.com.citrix': base_modules_mock,
    'nssrc.com.citrix.netscaler': base_modules_mock,
    'nssrc.com.citrix.netscaler.nitro': base_modules_mock,
    'nssrc.com.citrix.netscaler.nitro.resource': base_modules_mock,
    'nssrc.com.citrix.netscaler.nitro.resource.config': base_modules_mock,
    'nssrc.com.citrix.netscaler.nitro.exception': base_modules_mock,
    'nssrc.com.citrix.netscaler.nitro.exception.nitro_exception': base_modules_mock,
    'nssrc.com.citrix.netscaler.nitro.exception.nitro_exception.nitro_exception': nitro_exception_mock,
    'nssrc.com.citrix.netscaler.nitro.service': base_modules_mock,
    'nssrc.com.citrix.netscaler.nitro.service.nitro_service': base_modules_mock,
    'nssrc.com.citrix.netscaler.nitro.service.nitro_service.nitro_service': nitro_service_mock,
}

nitro_base_patcher = patch.dict(sys.modules, base_modules_to_mock)


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


class TestModule(unittest.TestCase):
    def failed(self):
        def fail_json(*args, **kwargs):
            kwargs['failed'] = True
            raise AnsibleFailJson(kwargs)

        with patch.object(basic.AnsibleModule, 'fail_json', fail_json):
            with self.assertRaises(AnsibleFailJson) as exc:
                self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def exited(self, changed=False):
        def exit_json(*args, **kwargs):
            raise AnsibleExitJson(kwargs)

        with patch.object(basic.AnsibleModule, 'exit_json', exit_json):
            with self.assertRaises(AnsibleExitJson) as exc:
                self.module.main()

        result = exc.exception.args[0]
        return result

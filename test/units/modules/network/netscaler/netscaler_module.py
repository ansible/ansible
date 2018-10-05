import sys

from ansible.compat.tests.mock import patch, Mock
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase

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


class TestModule(ModuleTestCase):
    def failed(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def exited(self, changed=False):
        with self.assertRaises(AnsibleExitJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        return result

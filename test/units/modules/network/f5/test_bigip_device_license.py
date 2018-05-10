# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_device_license import ApiParameters
    from library.modules.bigip_device_license import ModuleParameters
    from library.modules.bigip_device_license import ModuleManager
    from library.modules.bigip_device_license import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_device_license import ApiParameters
        from ansible.modules.network.f5.bigip_device_license import ModuleParameters
        from ansible.modules.network.f5.bigip_device_license import ModuleManager
        from ansible.modules.network.f5.bigip_device_license import ArgumentSpec
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            license_key='xxxx-yyyy-zzzz',
            license_server='foo-license.f5.com',
            accept_eula=True
        )

        p = ModuleParameters(params=args)
        assert p.license_key == 'xxxx-yyyy-zzzz'
        assert p.license_server == 'foo-license.f5.com'
        assert p.accept_eula is True


class TestModuleManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_create(self, *args):
        set_module_args(
            dict(
                license_key='xxxx-yyyy-zzzz',
                license_server='foo-license.f5.com',
                accept_eula=True,
                server='localhost',
                user='admin',
                password='password'
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.read_dossier_from_device = Mock(return_value=True)
        mm.generate_license_from_remote = Mock(return_value=True)
        mm.upload_license_to_device = Mock(return_value=True)
        mm.upload_eula_to_device = Mock(return_value=True)
        mm.reload_license = Mock(return_value=True)
        mm._is_mcpd_ready_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True

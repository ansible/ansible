# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigiq_regkey_license_assignment import ApiParameters
    from library.modules.bigiq_regkey_license_assignment import ModuleParameters
    from library.modules.bigiq_regkey_license_assignment import ModuleManager
    from library.modules.bigiq_regkey_license_assignment import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigiq_regkey_license_assignment import ApiParameters
        from ansible.modules.network.f5.bigiq_regkey_license_assignment import ModuleParameters
        from ansible.modules.network.f5.bigiq_regkey_license_assignment import ModuleManager
        from ansible.modules.network.f5.bigiq_regkey_license_assignment import ArgumentSpec
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
    def test_module_parameters_unmanaged(self):
        args = dict(
            pool='foo-pool',
            key='XXXX-XXXX-XXXX-XXXX-XXXX',
            device='1.1.1.1',
            managed=False,
            device_username='admin',
            device_password='secret',
            device_port='8443'
        )

        p = ModuleParameters(params=args)
        assert p.pool == 'foo-pool'
        assert p.key == 'XXXX-XXXX-XXXX-XXXX-XXXX'
        assert p.device == '1.1.1.1'
        assert p.managed is False
        assert p.device_username == 'admin'
        assert p.device_password == 'secret'
        assert p.device_port == 8443

    def test_module_parameters_managed(self):
        args = dict(
            pool='foo-pool',
            key='XXXX-XXXX-XXXX-XXXX-XXXX',
            device='1.1.1.1',
            managed=True,
        )

        p = ModuleParameters(params=args)
        assert p.pool == 'foo-pool'
        assert p.key == 'XXXX-XXXX-XXXX-XXXX-XXXX'
        assert p.device == '1.1.1.1'
        assert p.managed is True


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            pool='foo-pool',
            key='XXXX-XXXX-XXXX-XXXX-XXXX',
            device='1.1.1.1',
            device_username='admin',
            device_password='secret',
            managed='no',
            state='present',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)
        mm.wait_for_device_to_be_licensed = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

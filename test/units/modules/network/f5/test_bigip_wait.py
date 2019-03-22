# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_wait import Parameters
    from library.modules.bigip_wait import ModuleManager
    from library.modules.bigip_wait import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_wait import Parameters
    from ansible.modules.network.f5.bigip_wait import ModuleManager
    from ansible.modules.network.f5.bigip_wait import ArgumentSpec

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock
    from units.compat.mock import patch

    from units.modules.utils import set_module_args


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
            delay=3,
            timeout=500,
            sleep=10,
            msg='We timed out during waiting for BIG-IP :-('
        )

        p = Parameters(params=args)
        assert p.delay == 3
        assert p.timeout == 500
        assert p.sleep == 10
        assert p.msg == 'We timed out during waiting for BIG-IP :-('

    def test_module_string_parameters(self):
        args = dict(
            delay='3',
            timeout='500',
            sleep='10',
            msg='We timed out during waiting for BIG-IP :-('
        )

        p = Parameters(params=args)
        assert p.delay == 3
        assert p.timeout == 500
        assert p.sleep == 10
        assert p.msg == 'We timed out during waiting for BIG-IP :-('


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_wait_already_available(self, *args):
        set_module_args(dict(
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm._connect_to_device = Mock(return_value=True)
        mm._device_is_rebooting = Mock(return_value=False)
        mm._is_mprov_running_on_device = Mock(return_value=False)
        mm._get_client_connection = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is False
        assert results['elapsed'] == 0

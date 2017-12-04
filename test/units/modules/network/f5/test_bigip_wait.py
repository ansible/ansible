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

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import F5ModuleError

try:
    from library.bigip_wait import Parameters
    from library.bigip_wait import ModuleManager
    from library.bigip_wait import ArgumentSpec
    from library.bigip_wait import AnsibleF5ClientStub
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_wait import Parameters
        from ansible.modules.network.f5.bigip_wait import ModuleManager
        from ansible.modules.network.f5.bigip_wait import ArgumentSpec
        from ansible.modules.network.f5.bigip_wait import AnsibleF5ClientStub
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
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
            delay=3,
            timeout=500,
            sleep=10,
            msg='We timed out during waiting for BIG-IP :-('
        )

        p = Parameters(args)
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

        p = Parameters(args)
        assert p.delay == 3
        assert p.timeout == 500
        assert p.sleep == 10
        assert p.msg == 'We timed out during waiting for BIG-IP :-('


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_wait_already_available(self, *args):
        set_module_args(dict(
            password='passsword',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5ClientStub(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm._connect_to_device = Mock(return_value=True)
        mm._device_is_rebooting = Mock(return_value=False)
        mm._is_mprov_running_on_device = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is False
        assert results['elapsed'] == 1

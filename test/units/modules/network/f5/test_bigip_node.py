# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
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
    from library.modules.bigip_node import Parameters
    from library.modules.bigip_node import ModuleParameters
    from library.modules.bigip_node import ApiParameters
    from library.modules.bigip_node import ModuleManager
    from library.modules.bigip_node import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_node import Parameters
        from ansible.modules.network.f5.bigip_node import ModuleParameters
        from ansible.modules.network.f5.bigip_node import ApiParameters
        from ansible.modules.network.f5.bigip_node import ModuleManager
        from ansible.modules.network.f5.bigip_node import ArgumentSpec
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
            host='10.20.30.40',
            name='10.20.30.40'
        )

        p = Parameters(params=args)
        assert p.host == '10.20.30.40'
        assert p.name == '10.20.30.40'

    def test_api_parameters(self):
        args = load_fixture('load_ltm_node_1.json')

        p = Parameters(params=args)
        assert p.address == '1.2.3.4'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_node(self, *args):
        set_module_args(dict(
            host='10.20.30.40',
            name='mytestserver',
            monitors=[
                '/Common/icmp'
            ],
            partition='Common',
            state='present',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_selfip_idempotent(self, *args):
        set_module_args(dict(
            host='10.20.30.40',
            name='mytestserver',
            monitors=[
                '/Common/icmp'
            ],
            partition='Common',
            state='present',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        current = Parameters(params=load_fixture('load_ltm_node_3.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, True])
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_create_node_fqdn(self, *args):
        set_module_args(dict(
            fqdn='foo.bar',
            name='mytestserver',
            monitors=[
                '/Common/icmp'
            ],
            partition='Common',
            state='present',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_update_node_fqdn_up_interval(self, *args):
        set_module_args(dict(
            fqdn='foo.bar',
            fqdn_up_interval=100,
            name='mytestserver',
            monitors=[
                '/Common/icmp'
            ],
            partition='Common',
            state='present',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        current = ApiParameters(params=load_fixture('load_ltm_node_2.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, True])
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_update_node_fqdn_up_interval_idempotent(self, *args):
        set_module_args(dict(
            fqdn='google.com',
            fqdn_up_interval=3600,
            name='fqdn-foo',
            monitors=[
                'icmp',
                'tcp_echo'
            ],
            partition='Common',
            state='present',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        current = ApiParameters(params=load_fixture('load_ltm_node_2.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, True])
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is not True

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

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_monitor_dns import ApiParameters
    from library.modules.bigip_monitor_dns import ModuleParameters
    from library.modules.bigip_monitor_dns import ModuleManager
    from library.modules.bigip_monitor_dns import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_monitor_dns import ApiParameters
    from ansible.modules.network.f5.bigip_monitor_dns import ModuleParameters
    from ansible.modules.network.f5.bigip_monitor_dns import ModuleManager
    from ansible.modules.network.f5.bigip_monitor_dns import ArgumentSpec

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
            parent='/Common/dns',
            interval=10,
            time_until_up=0,
            timeout=30,
        )

        p = ModuleParameters(params=args)
        assert p.parent == '/Common/dns'
        assert p.interval == 10
        assert p.time_until_up == 0
        assert p.timeout == 30

    def test_api_parameters(self):
        args = dict(
            defaultsFrom='/Common/dns',
            interval=10,
            timeUntilUp=0,
            timeout=30,
        )

        p = ApiParameters(params=args)
        assert p.parent == '/Common/dns'
        assert p.interval == 10
        assert p.time_until_up == 0
        assert p.timeout == 30


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            name='foo',
            parent='/Common/dns',
            query_name='foo',
            interval=20,
            timeout=30,
            time_until_up=60,
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

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_with_description(self, *args):
        set_module_args(dict(
            name='foo',
            parent='/Common/dns',
            query_name='foo',
            interval=20,
            timeout=30,
            time_until_up=60,
            description='Important Description',
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

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

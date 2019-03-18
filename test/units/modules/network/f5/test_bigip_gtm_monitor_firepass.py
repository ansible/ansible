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
    from library.modules.bigip_gtm_monitor_firepass import ApiParameters
    from library.modules.bigip_gtm_monitor_firepass import ModuleParameters
    from library.modules.bigip_gtm_monitor_firepass import ModuleManager
    from library.modules.bigip_gtm_monitor_firepass import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_gtm_monitor_firepass import ApiParameters
    from ansible.modules.network.f5.bigip_gtm_monitor_firepass import ModuleParameters
    from ansible.modules.network.f5.bigip_gtm_monitor_firepass import ModuleManager
    from ansible.modules.network.f5.bigip_gtm_monitor_firepass import ArgumentSpec

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
            name='foo',
            parent='/Common/my-http',
            max_load_average='60',
            concurrency_limit='70',
            ip='1.1.1.1',
            port='80',
            interval='10',
            timeout='20',
            ignore_down_response=True,
            probe_timeout='30'
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.parent == '/Common/my-http'
        assert p.max_load_average == 60
        assert p.concurrency_limit == 70
        assert p.destination == '1.1.1.1:80'
        assert p.ip == '1.1.1.1'
        assert p.port == 80
        assert p.interval == 10
        assert p.timeout == 20
        assert p.ignore_down_response is True
        assert p.probe_timeout == 30

    def test_api_parameters(self):
        args = load_fixture('load_gtm_monitor_firepass_1.json')

        p = ApiParameters(params=args)
        assert p.name == 'foo'
        assert p.parent == '/Common/firepass_gtm'
        assert p.max_load_average == 12
        assert p.concurrency_limit == 95
        assert p.destination == '1.1.1.1:80'
        assert p.ip == '1.1.1.1'
        assert p.port == 80
        assert p.interval == 30
        assert p.timeout == 90
        assert p.ignore_down_response is True
        assert p.probe_timeout == 5


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

        try:
            self.p1 = patch('library.modules.bigip_gtm_monitor_firepass.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_gtm_monitor_firepass.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True

    def tearDown(self):
        self.p1.stop()

    def test_create_monitor(self, *args):
        set_module_args(dict(
            name='foo',
            ip='10.10.10.10',
            port=80,
            interval=20,
            timeout=30,
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
        mm.module_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

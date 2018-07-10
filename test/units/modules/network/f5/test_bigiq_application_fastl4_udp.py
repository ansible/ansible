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
    from library.modules.bigiq_application_fastl4_udp import ApiParameters
    from library.modules.bigiq_application_fastl4_udp import ModuleParameters
    from library.modules.bigiq_application_fastl4_udp import ModuleManager
    from library.modules.bigiq_application_fastl4_udp import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigiq_application_fastl4_udp import ApiParameters
        from ansible.modules.network.f5.bigiq_application_fastl4_udp import ModuleParameters
        from ansible.modules.network.f5.bigiq_application_fastl4_udp import ModuleManager
        from ansible.modules.network.f5.bigiq_application_fastl4_udp import ArgumentSpec
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
            name='foo',
            description='my description',
            service_environment='bar',
            servers=[
                dict(
                    address='1.2.3.4',
                    port=8080
                ),
                dict(
                    address='5.6.7.8',
                    port=8000
                )
            ],
            inbound_virtual=dict(
                address='2.2.2.2',
                netmask='255.255.255.255',
                port=80
            )
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.config_set_name == 'foo'
        assert p.sub_path == 'foo'
        assert p.http_profile == 'profile_http'
        assert p.service_environment == 'bar'
        assert len(p.servers) == 2
        assert 'address' in p.servers[0]
        assert 'port' in p.servers[0]
        assert 'address' in p.servers[1]
        assert 'port' in p.servers[1]
        assert p.servers[0]['address'] == '1.2.3.4'
        assert p.servers[0]['port'] == 8080
        assert p.servers[1]['address'] == '5.6.7.8'
        assert p.servers[1]['port'] == 8000
        assert 'address' in p.inbound_virtual
        assert 'netmask' in p.inbound_virtual
        assert 'port' in p.inbound_virtual
        assert p.inbound_virtual['address'] == '2.2.2.2'
        assert p.inbound_virtual['netmask'] == '255.255.255.255'
        assert p.inbound_virtual['port'] == 80


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_create(self, *args):
        set_module_args(dict(
            name='foo',
            description='my description',
            service_environment='bar',
            servers=[
                dict(
                    address='1.2.3.4',
                    port=8080
                ),
                dict(
                    address='5.6.7.8',
                    port=8000
                )
            ],
            inbound_virtual=dict(
                address='2.2.2.2',
                netmask='255.255.255.255',
                port=80
            ),
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
        mm.has_no_service_environment = Mock(return_value=False)
        mm.wait_for_apply_template_task = Mock(return_value=True)

        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(side_effect=[False, True])

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'my description'

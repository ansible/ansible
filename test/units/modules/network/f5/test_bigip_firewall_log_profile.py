# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
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
    from library.modules.bigip_firewall_log_profile import ApiParameters
    from library.modules.bigip_firewall_log_profile import ModuleParameters
    from library.modules.bigip_firewall_log_profile import ModuleManager
    from library.modules.bigip_firewall_log_profile import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_firewall_log_profile import ApiParameters
    from ansible.modules.network.f5.bigip_firewall_log_profile import ModuleParameters
    from ansible.modules.network.f5.bigip_firewall_log_profile import ModuleManager
    from ansible.modules.network.f5.bigip_firewall_log_profile import ArgumentSpec

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock

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
            description='my description',
            partition='Common',
            ip_intelligence=dict(
                log_publisher='foobar',
                rate_limit='300000',
                log_translation_fields='yes',
                log_rtbh='yes',
                log_shun='yes',
            ),
            port_misuse=dict(
                log_publisher='/Part/bazbar',
                rate_limit='indefinite',
            ),
            dos_protection=dict(
                sip_publisher='sip-pub',
                dns_publisher='/Temp/dns-pub',
                network_publisher='net-pub'
            )
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'my description'
        assert p.ip_rate_limit == 300000
        assert p.ip_log_publisher == '/Common/foobar'
        assert p.ip_log_translation_fields == 'enabled'
        assert p.ip_log_shun is None
        assert p.ip_log_rtbh == 'enabled'
        assert p.port_log_publisher == '/Part/bazbar'
        assert p.port_rate_limit == 4294967295
        assert p.dns_publisher == '/Temp/dns-pub'
        assert p.sip_publisher == '/Common/sip-pub'
        assert p.network_publisher == '/Common/net-pub'

    def test_api_parameters(self):
        args = load_fixture('load_afm_log_global_network_profile.json')

        p = ApiParameters(params=args)
        assert p.name == 'global-network'
        assert p.description == 'Default logging profile for network events'
        assert p.ip_log_shun == 'disabled'
        assert p.ip_log_translation_fields == 'disabled'
        assert p.ip_rate_limit == 4294967295
        assert p.port_rate_limit == 4294967295
        assert p.ip_log_publisher is None
        assert p.port_log_publisher is None


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            name='foo',
            description='this is a description',
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
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'this is a description'

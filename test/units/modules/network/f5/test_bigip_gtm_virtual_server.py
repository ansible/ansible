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
    from library.modules.bigip_gtm_virtual_server import ApiParameters
    from library.modules.bigip_gtm_virtual_server import ModuleParameters
    from library.modules.bigip_gtm_virtual_server import ModuleManager
    from library.modules.bigip_gtm_virtual_server import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_gtm_virtual_server import ApiParameters
    from ansible.modules.network.f5.bigip_gtm_virtual_server import ModuleParameters
    from ansible.modules.network.f5.bigip_gtm_virtual_server import ModuleManager
    from ansible.modules.network.f5.bigip_gtm_virtual_server import ArgumentSpec

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
            server_name='server1',
            address='1.1.1.1',
            port=22,
            translation_address='2.2.2.2',
            translation_port=443,
            availability_requirements=dict(
                type='at_least',
                at_least=2,
            ),
            monitors=['http', 'tcp', 'gtp'],
            virtual_server_dependencies=[
                dict(
                    server='server2',
                    virtual_server='vs2'
                )
            ],
            link='link1',
            limits=dict(
                bits_enabled=True,
                packets_enabled=True,
                connections_enabled=True,
                bits_limit=100,
                packets_limit=200,
                connections_limit=300
            ),
            state='present'
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.server_name == 'server1'
        assert p.address == '1.1.1.1'
        assert p.port == 22
        assert p.translation_address == '2.2.2.2'
        assert p.translation_port == 443
        assert p.availability_requirement_type == 'at_least'
        assert p.at_least == 2
        assert p.monitors == 'min 2 of { /Common/http /Common/tcp /Common/gtp }'
        assert len(p.virtual_server_dependencies) == 1
        assert p.link == '/Common/link1'
        assert p.bits_enabled == 'enabled'
        assert p.bits_limit == 100
        assert p.packets_enabled == 'enabled'
        assert p.packets_limit == 200
        assert p.connections_enabled == 'enabled'
        assert p.connections_limit == 300

    def test_api_parameters(self):
        args = load_fixture('load_gtm_server_virtual_2.json')

        p = ApiParameters(params=args)
        assert p.name == 'vs2'
        assert p.address == '6.6.6.6'
        assert p.port == 8080
        assert p.translation_address == 'none'
        assert p.translation_port == 0
        assert p.availability_requirement_type == 'all'
        assert p.monitors == '/Common/gtp'
        assert p.bits_enabled == 'enabled'
        assert p.bits_limit == 100
        assert p.packets_enabled == 'enabled'
        assert p.packets_limit == 200
        assert p.connections_enabled == 'enabled'
        assert p.connections_limit == 300


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

        try:
            self.p1 = patch('library.modules.bigip_gtm_virtual_server.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_gtm_virtual_server.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True

    def tearDown(self):
        self.p1.stop()

    def test_create_datacenter(self, *args):
        set_module_args(dict(
            server_name='foo',
            name='vs1',
            address='1.1.1.1',
            state='present',
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

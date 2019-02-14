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
    from library.modules.bigip_gtm_pool_member import ApiParameters
    from library.modules.bigip_gtm_pool_member import ModuleParameters
    from library.modules.bigip_gtm_pool_member import ModuleManager
    from library.modules.bigip_gtm_pool_member import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_gtm_pool_member import ApiParameters
    from ansible.modules.network.f5.bigip_gtm_pool_member import ModuleParameters
    from ansible.modules.network.f5.bigip_gtm_pool_member import ModuleManager
    from ansible.modules.network.f5.bigip_gtm_pool_member import ArgumentSpec

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
            pool='pool1',
            server_name='server1',
            virtual_server='vs1',
            type='a',
            state='enabled',
            limits=dict(
                bits_enabled=True,
                packets_enabled=True,
                connections_enabled=True,
                bits_limit=100,
                packets_limit=200,
                connections_limit=300
            ),
            description='foo description',
            ratio=10,
            monitor='tcp',
            member_order=2
        )

        p = ModuleParameters(params=args)
        assert p.pool == 'pool1'
        assert p.server_name == 'server1'
        assert p.virtual_server == 'vs1'
        assert p.type == 'a'
        assert p.state == 'enabled'
        assert p.bits_enabled == 'enabled'
        assert p.packets_enabled == 'enabled'
        assert p.connections_enabled == 'enabled'
        assert p.bits_limit == 100
        assert p.packets_limit == 200
        assert p.connections_limit == 300

    def test_api_parameters(self):
        args = load_fixture('load_gtm_pool_a_member_1.json')

        p = ApiParameters(params=args)
        assert p.ratio == 1
        assert p.monitor == 'default'
        assert p.member_order == 1
        assert p.packets_enabled == 'disabled'
        assert p.packets_limit == 0
        assert p.bits_enabled == 'disabled'
        assert p.bits_limit == 0
        assert p.connections_enabled == 'disabled'
        assert p.connections_limit == 0


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

        try:
            self.p1 = patch('library.modules.bigip_gtm_pool_member.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_gtm_pool_member.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True

    def tearDown(self):
        self.p1.stop()

    def test_create_monitor(self, *args):
        set_module_args(dict(
            pool='pool1',
            server_name='server1',
            virtual_server='vs1',
            type='a',
            state='enabled',
            limits=dict(
                bits_enabled='yes',
                packets_enabled='yes',
                connections_enabled='yes',
                bits_limit=100,
                packets_limit=200,
                connections_limit=300
            ),
            description='foo description',
            ratio=10,
            monitor='tcp',
            member_order=2,
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
            required_one_of=self.spec.required_one_of,
            required_together=self.spec.required_together,
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)
        mm.module_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_aggregate_pool_members(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            type='a',
            aggregate=[
                dict(
                    server_name='my-name1',
                    virtual_server='some-vs2',
                    state='present',
                    partition='Common',

                ),
                dict(
                    server_name='my-name1',
                    virtual_server='some-vs1',
                    state='present',
                    partition='Common'
                )
            ],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
            required_one_of=self.spec.required_one_of,
            required_together=self.spec.required_together,
        )

        mm = ModuleManager(module=module)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True

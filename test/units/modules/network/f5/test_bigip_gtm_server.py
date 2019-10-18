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
    from library.modules.bigip_gtm_server import ApiParameters
    from library.modules.bigip_gtm_server import ModuleParameters
    from library.modules.bigip_gtm_server import ModuleManager
    from library.modules.bigip_gtm_server import V1Manager
    from library.modules.bigip_gtm_server import V2Manager
    from library.modules.bigip_gtm_server import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_gtm_server import ApiParameters
    from ansible.modules.network.f5.bigip_gtm_server import ModuleParameters
    from ansible.modules.network.f5.bigip_gtm_server import ModuleManager
    from ansible.modules.network.f5.bigip_gtm_server import V1Manager
    from ansible.modules.network.f5.bigip_gtm_server import V2Manager
    from ansible.modules.network.f5.bigip_gtm_server import ArgumentSpec

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
            name='GTM_Server',
            datacenter='New York',
            partition='Common',
            server_type='bigip',
            link_discovery='disabled',
            virtual_server_discovery='disabled',
            devices=[
                dict(
                    name='server_1',
                    address='1.1.1.1'
                ),
                dict(
                    name='server_2',
                    address='2.2.2.1',
                    translation='192.168.2.1'
                ),
                dict(
                    name='server_2',
                    address='2.2.2.2'
                ),
                dict(
                    name='server_3',
                    addresses=[
                        dict(
                            address='3.3.3.1'
                        ),
                        dict(
                            address='3.3.3.2'
                        )
                    ]
                ),
                dict(
                    name='server_4',
                    addresses=[
                        dict(
                            address='4.4.4.1',
                            translation='192.168.14.1'
                        ),
                        dict(
                            address='4.4.4.2'
                        )
                    ]
                )
            ]
        )

        p = ModuleParameters(params=args)
        assert p.name == 'GTM_Server'
        assert p.datacenter == '/Common/New York'
        assert p.server_type == 'bigip'
        assert p.link_discovery == 'disabled'
        assert p.virtual_server_discovery == 'disabled'

    def test_api_parameters(self):
        args = load_fixture('load_gtm_server_1.json')

        p = ApiParameters(params=args)
        assert p.name == 'baz'
        assert p.datacenter == '/Common/foo'
        assert p.server_type == 'bigip'
        assert p.link_discovery == 'disabled'
        assert p.virtual_server_discovery == 'disabled'


class TestV1Manager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

        try:
            self.p1 = patch('library.modules.bigip_gtm_server.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_gtm_server.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True

        try:
            self.p2 = patch('library.modules.bigip_gtm_server.tmos_version')
            self.m2 = self.p2.start()
            self.m2.return_value = '13.0.0'
        except Exception:
            self.p2 = patch('ansible.modules.network.f5.bigip_gtm_server.tmos_version')
            self.m2 = self.p2.start()
            self.m2.return_value = '13.0.0'

    def tearDown(self):
        self.p1.stop()
        self.p2.stop()

    def test_create(self, *args):
        set_module_args(dict(
            name='GTM_Server',
            datacenter='/Common/New York',
            server_type='bigip',
            link_discovery='disabled',
            virtual_server_discovery='disabled',
            devices=[
                dict(
                    name='server_1',
                    address='1.1.1.1'
                ),
                dict(
                    name='server_2',
                    address='2.2.2.1',
                    translation='192.168.2.1'
                ),
                dict(
                    name='server_2',
                    address='2.2.2.2'
                ),
                dict(
                    name='server_3',
                    addresses=[
                        dict(
                            address='3.3.3.1'
                        ),
                        dict(
                            address='3.3.3.2'
                        )
                    ]
                ),
                dict(
                    name='server_4',
                    addresses=[
                        dict(
                            address='4.4.4.1',
                            translation='192.168.14.1'
                        ),
                        dict(
                            address='4.4.4.2'
                        )
                    ]
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
            supports_check_mode=self.spec.supports_check_mode
        )

        m1 = V1Manager(module=module, params=module.params)
        m1.exists = Mock(side_effect=[False, True])
        m1.create_on_device = Mock(return_value=True)
        m1.client = Mock()
        m1.client.api.tmos_version = '12.0.0'

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=m1)
        mm.version_is_less_than = Mock(return_value=True)
        mm.gtm_provisioned = Mock(return_value=True)
        mm.module_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['server_type'] == 'bigip'


class TestV2Manager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

        try:
            self.p1 = patch('library.modules.bigip_gtm_server.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_gtm_server.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True

        try:
            self.p2 = patch('library.modules.bigip_gtm_server.tmos_version')
            self.m2 = self.p2.start()
            self.m2.return_value = '13.0.0'
        except Exception:
            self.p2 = patch('ansible.modules.network.f5.bigip_gtm_server.tmos_version')
            self.m2 = self.p2.start()
            self.m2.return_value = '13.0.0'

    def tearDown(self):
        self.p1.stop()
        self.p2.stop()

    def test_create(self, *args):
        set_module_args(dict(
            name='GTM_Server',
            datacenter='/Common/New York',
            server_type='bigip',
            link_discovery='disabled',
            virtual_server_discovery='disabled',
            devices=[
                dict(
                    name='server_1',
                    address='1.1.1.1'
                ),
                dict(
                    name='server_2',
                    address='2.2.2.1',
                    translation='192.168.2.1'
                ),
                dict(
                    name='server_2',
                    address='2.2.2.2'
                ),
                dict(
                    name='server_3',
                    addresses=[
                        dict(
                            address='3.3.3.1'
                        ),
                        dict(
                            address='3.3.3.2'
                        )
                    ]
                ),
                dict(
                    name='server_4',
                    addresses=[
                        dict(
                            address='4.4.4.1',
                            translation='192.168.14.1'
                        ),
                        dict(
                            address='4.4.4.2'
                        )
                    ]
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
            supports_check_mode=self.spec.supports_check_mode
        )

        m1 = V2Manager(module=module)
        m1.exists = Mock(side_effect=[False, True])
        m1.create_on_device = Mock(return_value=True)
        m1.client = Mock()
        m1.client.api.tmos_version = '13.1.0'

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=m1)
        mm.version_is_less_than = Mock(return_value=False)
        mm.gtm_provisioned = Mock(return_value=True)
        mm.module_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['server_type'] == 'bigip'

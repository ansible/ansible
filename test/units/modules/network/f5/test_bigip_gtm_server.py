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
    from library.bigip_gtm_server import ApiParameters
    from library.bigip_gtm_server import ModuleParameters
    from library.bigip_gtm_server import ModuleManager
    from library.bigip_gtm_server import V1Manager
    from library.bigip_gtm_server import V2Manager
    from library.bigip_gtm_server import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_gtm_server import ApiParameters
        from ansible.modules.network.f5.bigip_gtm_server import ModuleParameters
        from ansible.modules.network.f5.bigip_gtm_server import ModuleManager
        from ansible.modules.network.f5.bigip_gtm_server import V1Manager
        from ansible.modules.network.f5.bigip_gtm_server import V2Manager
        from ansible.modules.network.f5.bigip_gtm_server import ArgumentSpec
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

        p = ModuleParameters(args)
        assert p.name == 'GTM_Server'
        assert p.datacenter == '/Common/New York'
        assert p.server_type == 'bigip'
        assert p.link_discovery == 'disabled'
        assert p.virtual_server_discovery == 'disabled'

    def test_api_parameters(self):
        args = load_fixture('load_gtm_server_1.json')

        p = ApiParameters(args)
        assert p.name == 'baz'
        assert p.datacenter == '/Common/foo'
        assert p.server_type == 'bigip'
        assert p.link_discovery == 'disabled'
        assert p.virtual_server_discovery == 'disabled'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestV1Manager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            server='lb.mydomain.com',
            user='admin',
            password='secret',
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
            ]
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        m1 = V1Manager(client)
        m1.exists = Mock(side_effect=[False, True])
        m1.create_on_device = Mock(return_value=True)

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=m1)
        mm.version_is_less_than = Mock(return_value=True)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['server_type'] == 'bigip'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestV2Manager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            server='lb.mydomain.com',
            user='admin',
            password='secret',
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
            ]
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        m1 = V2Manager(client)
        m1.exists = Mock(side_effect=[False, True])
        m1.create_on_device = Mock(return_value=True)

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=m1)
        mm.version_is_less_than = Mock(return_value=False)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['server_type'] == 'bigip'

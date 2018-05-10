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
    from library.modules.bigip_gtm_pool_member import ApiParameters
    from library.modules.bigip_gtm_pool_member import ModuleParameters
    from library.modules.bigip_gtm_pool_member import ModuleManager
    from library.modules.bigip_gtm_pool_member import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_gtm_pool_member import ApiParameters
        from ansible.modules.network.f5.bigip_gtm_pool_member import ModuleParameters
        from ansible.modules.network.f5.bigip_gtm_pool_member import ModuleManager
        from ansible.modules.network.f5.bigip_gtm_pool_member import ArgumentSpec
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


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

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
            server='localhost',
            password='password',
            user='admin'
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

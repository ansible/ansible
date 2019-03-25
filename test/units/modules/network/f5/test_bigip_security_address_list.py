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

pytestmark = []

if sys.version_info < (2, 7):
    pytestmark.append(pytest.mark.skip("F5 Ansible modules require Python >= 2.7"))

from units.compat import unittest
from units.compat.mock import Mock
from units.compat.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_security_address_list import ApiParameters
    from library.modules.bigip_security_address_list import ModuleParameters
    from library.modules.bigip_security_address_list import ModuleManager
    from library.modules.bigip_security_address_list import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_security_address_list import ApiParameters
        from ansible.modules.network.f5.bigip_security_address_list import ModuleParameters
        from ansible.modules.network.f5.bigip_security_address_list import ModuleManager
        from ansible.modules.network.f5.bigip_security_address_list import ArgumentSpec
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        pytestmark.append(pytest.mark.skip("F5 Ansible modules require the f5-sdk Python library"))


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
            description='this is a description',
            addresses=['1.1.1.1', '2.2.2.2'],
            address_ranges=['3.3.3.3-4.4.4.4', '5.5.5.5-6.6.6.6'],
            address_lists=['/Common/foo', 'foo']
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'this is a description'
        assert len(p.addresses) == 2
        assert len(p.address_ranges) == 2
        assert len(p.address_lists) == 2

    def test_api_parameters(self):
        args = load_fixture('load_security_address_list_1.json')

        p = ApiParameters(params=args)
        assert len(p.addresses) == 2
        assert len(p.address_ranges) == 2
        assert len(p.address_lists) == 1
        assert len(p.fqdns) == 1
        assert len(p.geo_locations) == 5
        assert sorted(p.addresses) == ['1.1.1.1', '2700:bc00:1f10:101::6']
        assert sorted(p.address_ranges) == ['2.2.2.2-3.3.3.3', '5.5.5.5-6.6.6.6']
        assert p.address_lists[0] == '/Common/foo'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            name='foo',
            description='this is a description',
            addresses=['1.1.1.1', '2.2.2.2'],
            address_ranges=['3.3.3.3-4.4.4.4', '5.5.5.5-6.6.6.6'],
            address_lists=['/Common/foo', 'foo'],
            geo_locations=[
                dict(country='US', region='Los Angeles'),
                dict(country='China'),
                dict(country='EU')
            ],
            fqdns=['google.com', 'mit.edu'],
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert 'addresses' in results
        assert 'address_lists' in results
        assert 'address_ranges' in results
        assert len(results['addresses']) == 2
        assert len(results['address_ranges']) == 2
        assert len(results['address_lists']) == 2
        assert results['description'] == 'this is a description'

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
    from library.modules.bigip_firewall_schedule import ApiParameters
    from library.modules.bigip_firewall_schedule import ModuleParameters
    from library.modules.bigip_firewall_schedule import ModuleManager
    from library.modules.bigip_firewall_schedule import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_firewall_schedule import ApiParameters
    from ansible.modules.network.f5.bigip_firewall_schedule import ModuleParameters
    from ansible.modules.network.f5.bigip_firewall_schedule import ModuleManager
    from ansible.modules.network.f5.bigip_firewall_schedule import ArgumentSpec

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
            daily_hour_end='21:00',
            daily_hour_start='11:00',
            date_valid_end='2019-03-11:15:30:00',
            date_valid_start='2019-03-01:15:30:00',
            days_of_week='all',
        )
        p = ModuleParameters(params=args)

        assert p.name == 'foo'
        assert p.description == 'my description'
        assert p.daily_hour_end == '21:00'
        assert p.daily_hour_start == '11:00'
        assert p.date_valid_end == '2019-03-11T15:30:00Z'
        assert p.date_valid_start == '2019-03-01T15:30:00Z'
        assert 'monday' in p.days_of_week

    def test_api_parameters(self):
        args = load_fixture('load_afm_schedule.json')

        p = ApiParameters(params=args)
        assert p.name == 'foobar'
        assert p.description == 'some description'
        assert p.daily_hour_end == '12:00'
        assert p.daily_hour_start == '6:00'
        assert p.date_valid_end == '2019-06-13T16:00:00Z'
        assert p.date_valid_start == '2019-05-31T07:00:00Z'
        assert 'sunday' in p.days_of_week


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

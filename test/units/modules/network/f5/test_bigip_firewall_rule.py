# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
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
    from library.modules.bigip_firewall_rule import ApiParameters
    from library.modules.bigip_firewall_rule import ModuleParameters
    from library.modules.bigip_firewall_rule import ModuleManager
    from library.modules.bigip_firewall_rule import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_firewall_rule import ApiParameters
        from ansible.modules.network.f5.bigip_firewall_rule import ModuleParameters
        from ansible.modules.network.f5.bigip_firewall_rule import ModuleManager
        from ansible.modules.network.f5.bigip_firewall_rule import ArgumentSpec
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
            parent_policy='policy1',
            protocol='tcp',
            source=[
                dict(address='1.2.3.4'),
                dict(address='::1'),
                dict(address_list='foo-list1'),
                dict(address_range='1.1.1.1-2.2.2.2.'),
                dict(vlan='vlan1'),
                dict(country='US'),
                dict(port='22'),
                dict(port_list='port-list1'),
                dict(port_range='80-443'),
            ],
            destination=[
                dict(address='1.2.3.4'),
                dict(address='::1'),
                dict(address_list='foo-list1'),
                dict(address_range='1.1.1.1-2.2.2.2.'),
                dict(country='US'),
                dict(port='22'),
                dict(port_list='port-list1'),
                dict(port_range='80-443'),
            ],
            irule='irule1',
            action='accept',
            logging=True,
        )

        p = ModuleParameters(params=args)
        assert p.irule == '/Common/irule1'
        assert p.action == 'accept'
        assert p.logging is True


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_monitor(self, *args):
        set_module_args(dict(
            name='foo',
            parent_policy='policy1',
            protocol='tcp',
            source=[
                dict(address='1.2.3.4'),
                dict(address='::1'),
                dict(address_list='foo-list1'),
                dict(address_range='1.1.1.1-2.2.2.2.'),
                dict(vlan='vlan1'),
                dict(country='US'),
                dict(port='22'),
                dict(port_list='port-list1'),
                dict(port_range='80-443'),
            ],
            destination=[
                dict(address='1.2.3.4'),
                dict(address='::1'),
                dict(address_list='foo-list1'),
                dict(address_range='1.1.1.1-2.2.2.2.'),
                dict(country='US'),
                dict(port='22'),
                dict(port_list='port-list1'),
                dict(port_range='80-443'),
            ],
            irule='irule1',
            action='accept',
            logging='yes',
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

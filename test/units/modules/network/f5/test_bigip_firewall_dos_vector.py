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

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_firewall_dos_vector import ModuleParameters
    from library.modules.bigip_firewall_dos_vector import ModuleManager
    from library.modules.bigip_firewall_dos_vector import ArgumentSpec
    from library.modules.bigip_firewall_dos_vector import ProtocolDnsManager

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_firewall_dos_vector import ModuleParameters
    from ansible.modules.network.f5.bigip_firewall_dos_vector import ModuleManager
    from ansible.modules.network.f5.bigip_firewall_dos_vector import ArgumentSpec
    from ansible.modules.network.f5.bigip_firewall_dos_vector import ProtocolDnsManager

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
            state='mitigate'
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.state == 'mitigate'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_dns(self, *args):
        set_module_args(dict(
            name='aaaa',
            state='mitigate',
            profile='foo',
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

        m1 = ProtocolDnsManager(module=module)
        m1.read_current_from_device = Mock(return_value=[])
        m1.update_on_device = Mock(return_value=True)

        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=m1)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

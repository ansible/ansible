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
    from library.modules.bigip_trunk import ApiParameters
    from library.modules.bigip_trunk import ModuleParameters
    from library.modules.bigip_trunk import ModuleManager
    from library.modules.bigip_trunk import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_trunk import ApiParameters
    from ansible.modules.network.f5.bigip_trunk import ModuleParameters
    from ansible.modules.network.f5.bigip_trunk import ModuleManager
    from ansible.modules.network.f5.bigip_trunk import ArgumentSpec

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
            interfaces=[
                '1.3', '1.1'
            ],
            link_selection_policy='auto',
            frame_distribution_hash='destination-mac',
            lacp_enabled=True,
            lacp_mode='active',
            lacp_timeout='long'
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.interfaces == ['1.1', '1.3']
        assert p.link_selection_policy == 'auto'
        assert p.frame_distribution_hash == 'dst-mac'
        assert p.lacp_enabled is True
        assert p.lacp_mode == 'active'
        assert p.lacp_timeout == 'long'

    def test_api_parameters(self):
        args = load_fixture('load_tm_net_trunk_1.json')

        p = ApiParameters(params=args)
        assert p.name == 'foo'
        assert p.frame_distribution_hash == 'dst-mac'
        assert p.lacp_enabled is False
        assert p.lacp_mode == 'active'
        assert p.lacp_timeout == 'long'
        assert p.interfaces == ['1.3']
        assert p.link_selection_policy == 'maximum-bandwidth'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            name='foo',
            interfaces=[
                '1.3', '1.1'
            ],
            link_selection_policy='auto',
            frame_distribution_hash='destination-mac',
            lacp_enabled=True,
            lacp_mode='active',
            lacp_timeout='long',
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

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['link_selection_policy'] == 'auto'
        assert results['frame_distribution_hash'] == 'destination-mac'
        assert results['lacp_enabled'] is True
        assert results['lacp_mode'] == 'active'
        assert results['lacp_timeout'] == 'long'

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
from ansible.module_utils.six import iteritems

try:
    from library.modules.bigip_device_facts import Parameters
    from library.modules.bigip_device_facts import VirtualAddressesFactManager
    from library.modules.bigip_device_facts import VirtualAddressesParameters
    from library.modules.bigip_device_facts import ArgumentSpec
    from library.modules.bigip_device_facts import ModuleManager

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_device_facts import Parameters
    from ansible.modules.network.f5.bigip_device_facts import VirtualAddressesFactManager
    from ansible.modules.network.f5.bigip_device_facts import VirtualAddressesParameters
    from ansible.modules.network.f5.bigip_device_facts import ArgumentSpec
    from ansible.modules.network.f5.bigip_device_facts import ModuleManager

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


class FakeVirtualAddress:
    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop('params', {})
        for key, value in iteritems(attrs):
            setattr(self, key, value)


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            gather_subset=['virtual-servers'],
        )
        p = Parameters(params=args)
        assert p.gather_subset == ['virtual-servers']


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

        try:
            self.p1 = patch('library.modules.bigip_device_facts.modules_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = ['ltm', 'gtm', 'asm']
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_device_facts.modules_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = ['ltm', 'gtm', 'asm']

    def tearDown(self):
        self.p1.stop()

    def test_get_trunk_facts(self, *args):
        set_module_args(dict(
            gather_subset=['virtual-addresses'],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        fixture1 = load_fixture('load_ltm_virtual_address_collection_1.json')
        collection = fixture1['items']

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        tm = VirtualAddressesFactManager(module=module)
        tm.read_collection_from_device = Mock(return_value=collection)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert 'virtual_addresses' in results
        assert len(results['virtual_addresses']) > 0

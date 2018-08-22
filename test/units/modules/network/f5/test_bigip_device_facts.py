# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

try:
    from library.modules.bigip_device_facts import Parameters
    from library.modules.bigip_device_facts import VirtualAddressesFactManager
    from library.modules.bigip_device_facts import VirtualAddressesParameters
    from library.modules.bigip_device_facts import ArgumentSpec
    from library.modules.bigip_device_facts import ModuleManager
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from f5.bigip.tm.gtm.pool import A
    from f5.utils.responses.handlers import Stats
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_device_pool import Parameters
        from ansible.modules.network.f5.bigip_device_pool import VirtualAddressesFactManager
        from ansible.modules.network.f5.bigip_device_pool import VirtualAddressesParameters
        from ansible.modules.network.f5.bigip_device_pool import ArgumentSpec
        from ansible.modules.network.f5.bigip_device_pool import ModuleManager
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from f5.bigip.tm.gtm.pool import A
        from f5.utils.responses.handlers import Stats
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


class FakeVirtualAddress(A):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop('attrs', {})
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

    def test_get_trunk_facts(self, *args):
        set_module_args(dict(
            gather_subset=['virtual-addresses'],
            password='password',
            server='localhost',
            user='admin'
        ))

        fixture1 = load_fixture('load_ltm_virtual_address_collection_1.json')
        collection = [FakeVirtualAddress(attrs=x) for x in fixture1['items']]

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

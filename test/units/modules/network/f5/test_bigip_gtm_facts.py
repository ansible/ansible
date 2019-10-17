# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys

import pytest

pytestmark = []

if sys.version_info < (2, 7):
    pytestmark.append(pytest.mark.skip("F5 Ansible modules require Python >= 2.7"))

from units.compat import unittest
from units.compat.mock import Mock
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

try:
    from library.modules.bigip_gtm_facts import Parameters
    from library.modules.bigip_gtm_facts import ModuleManager
    from library.modules.bigip_gtm_facts import PoolFactManager
    from library.modules.bigip_gtm_facts import TypedPoolFactManager
    from library.modules.bigip_gtm_facts import ArgumentSpec
    from f5.bigip.tm.gtm.pool import A
    from f5.utils.responses.handlers import Stats
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_gtm_pool import Parameters
        from ansible.modules.network.f5.bigip_gtm_pool import ModuleManager
        from ansible.modules.network.f5.bigip_gtm_pool import PoolFactManager
        from ansible.modules.network.f5.bigip_gtm_pool import TypedPoolFactManager
        from ansible.modules.network.f5.bigip_gtm_pool import ArgumentSpec
        from f5.bigip.tm.gtm.pool import A
        from f5.utils.responses.handlers import Stats
        from units.modules.utils import set_module_args
    except ImportError:
        pytestmark.append(pytest.mark.skip("F5 Ansible modules require the f5-sdk Python library"))
        # pytestmark will cause this test to skip but we have to define A so that classes can be
        # defined below
        A = object

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


class FakeStatResource(object):
    def __init__(self, obj):
        self.entries = obj


class FakeARecord(A):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop('attrs', {})
        for key, value in iteritems(attrs):
            setattr(self, key, value)


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            include=['pool'],
            filter='name.*'
        )
        p = Parameters(params=args)
        assert p.include == ['pool']
        assert p.filter == 'name.*'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_get_typed_pool_facts(self, *args):
        set_module_args(dict(
            include='pool',
            password='password',
            server='localhost',
            user='admin'
        ))

        fixture1 = load_fixture('load_gtm_pool_a_collection.json')
        fixture2 = load_fixture('load_gtm_pool_a_example_stats.json')
        collection = [FakeARecord(attrs=x) for x in fixture1['items']]
        stats = Stats(FakeStatResource(fixture2['entries']))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tfm = TypedPoolFactManager(module=module)
        tfm.read_collection_from_device = Mock(return_value=collection)
        tfm.read_stats_from_device = Mock(return_value=stats.stat)

        tm = PoolFactManager(module=module)
        tm.version_is_less_than_12 = Mock(return_value=False)
        tm.get_manager = Mock(return_value=tfm)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert 'pool' in results
        assert len(results['pool']) > 0
        assert 'load_balancing_mode' in results['pool'][0]

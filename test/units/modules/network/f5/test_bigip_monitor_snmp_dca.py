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

try:
    from library.modules.bigip_monitor_snmp_dca import Parameters
    from library.modules.bigip_monitor_snmp_dca import ModuleManager
    from library.modules.bigip_monitor_snmp_dca import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_monitor_snmp_dca import Parameters
    from ansible.modules.network.f5.bigip_monitor_snmp_dca import ModuleManager
    from ansible.modules.network.f5.bigip_monitor_snmp_dca import ArgumentSpec

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
            agent_type='UCD',
            community='public',
            cpu_coefficient='1.5',
            cpu_threshold='80',
            parent='/Common/snmp_dca',
            disk_coefficient='2.0',
            disk_threshold='90',
            interval=10,
            memory_coefficient='1.0',
            memory_threshold='70',
            time_until_up=0,
            timeout=30,
            version='v1'
        )

        p = Parameters(params=args)
        assert p.agent_type == 'UCD'
        assert p.community == 'public'
        assert p.cpu_coefficient == 1.5
        assert p.cpu_threshold == 80
        assert p.parent == '/Common/snmp_dca'
        assert p.disk_coefficient == 2.0
        assert p.disk_threshold == 90
        assert p.interval == 10
        assert p.memory_coefficient == 1.0
        assert p.memory_threshold == 70
        assert p.time_until_up == 0
        assert p.timeout == 30
        assert p.version == 'v1'

    def test_api_parameters(self):
        args = dict(
            agentType='UCD',
            community='public',
            cpuCoefficient='1.5',
            cpuThreshold='80',
            defaultsFrom='/Common/snmp_dca',
            diskCoefficient='2.0',
            diskThreshold='90',
            interval=10,
            memoryCoefficient='1.0',
            memoryThreshold='70',
            timeUntilUp=0,
            timeout=30,
            apiRawValues={
                "userDefined asdasd": "{ foo }",
                "userDefined bar": "tim rupp",
                "user-defined baz-": "nia",
                "userDefined userDefined": "23234"
            },
            version='v1'
        )

        p = Parameters(params=args)
        assert p.agent_type == 'UCD'
        assert p.community == 'public'
        assert p.cpu_coefficient == 1.5
        assert p.cpu_threshold == 80
        assert p.parent == '/Common/snmp_dca'
        assert p.disk_coefficient == 2.0
        assert p.disk_threshold == 90
        assert p.interval == 10
        assert p.memory_coefficient == 1.0
        assert p.memory_threshold == 70
        assert p.time_until_up == 0
        assert p.timeout == 30
        assert p.version == 'v1'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            name='foo',
            agent_type='UCD',
            community='public',
            cpu_coefficient='1.5',
            cpu_threshold='80',
            parent='/Common/snmp_dca',
            disk_coefficient='2.0',
            disk_threshold='90',
            memory_coefficient='1.0',
            memory_threshold='70',
            version='v1',
            interval=20,
            timeout=30,
            time_until_up=60,
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

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

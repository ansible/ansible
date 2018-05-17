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

try:
    from library.modules.bigip_iapp_service import Parameters
    from library.modules.bigip_iapp_service import ModuleManager
    from library.modules.bigip_iapp_service import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_iapp_service import Parameters
        from ansible.modules.network.f5.bigip_iapp_service import ModuleManager
        from ansible.modules.network.f5.bigip_iapp_service import ArgumentSpec
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

    def test_module_parameters_keys(self):
        args = load_fixture('create_iapp_service_parameters_f5_http.json')
        p = Parameters(params=args)

        # Assert the top-level keys
        assert p.name == 'http_example'
        assert p.partition == 'Common'
        assert p.template == '/Common/f5.http'
        assert p.deviceGroup == 'none'
        assert p.inheritedTrafficGroup == 'true'
        assert p.inheritedDevicegroup == 'true'
        assert p.traffic_group == '/Common/traffic-group-local-only'

    def test_module_parameters_lists(self):
        args = load_fixture('create_iapp_service_parameters_f5_http.json')
        p = Parameters(params=args)

        assert 'lists' in p._values

        assert p.lists[0]['name'] == 'irules__irules'
        assert p.lists[0]['encrypted'] == 'no'
        assert len(p.lists[0]['value']) == 1
        assert p.lists[0]['value'][0] == '/Common/lgyft'

        assert p.lists[1]['name'] == 'net__client_vlan'
        assert p.lists[1]['encrypted'] == 'no'
        assert len(p.lists[1]['value']) == 1
        assert p.lists[1]['value'][0] == '/Common/net2'

    def test_module_parameters_tables(self):
        args = load_fixture('create_iapp_service_parameters_f5_http.json')
        p = Parameters(params=args)

        assert 'tables' in p._values

        assert 'columnNames' in p.tables[0]
        assert len(p.tables[0]['columnNames']) == 1
        assert p.tables[0]['columnNames'][0] == 'name'

        assert 'name' in p.tables[0]
        assert p.tables[0]['name'] == 'pool__hosts'

        assert 'rows' in p.tables[0]
        assert len(p.tables[0]['rows']) == 1
        assert 'row' in p.tables[0]['rows'][0]
        assert len(p.tables[0]['rows'][0]['row']) == 1
        assert p.tables[0]['rows'][0]['row'][0] == 'demo.example.com'

        assert len(p.tables[1]['rows']) == 2
        assert 'row' in p.tables[0]['rows'][0]
        assert len(p.tables[1]['rows'][0]['row']) == 2
        assert p.tables[1]['rows'][0]['row'][0] == '10.1.1.1'
        assert p.tables[1]['rows'][0]['row'][1] == '0'
        assert p.tables[1]['rows'][1]['row'][0] == '10.1.1.2'
        assert p.tables[1]['rows'][1]['row'][1] == '0'

    def test_module_parameters_variables(self):
        args = load_fixture('create_iapp_service_parameters_f5_http.json')
        p = Parameters(params=args)

        assert 'variables' in p._values
        assert len(p.variables) == 34

        # Assert one configuration value
        assert 'name' in p.variables[0]
        assert 'value' in p.variables[0]
        assert p.variables[0]['name'] == 'afm__dos_security_profile'
        assert p.variables[0]['value'] == '/#do_not_use#'

        # Assert a second configuration value
        assert 'name' in p.variables[1]
        assert 'value' in p.variables[1]
        assert p.variables[1]['name'] == 'afm__policy'
        assert p.variables[1]['value'] == '/#do_not_use#'

    def test_module_strict_updates_from_top_level(self):
        # Assumes the user did not provide any parameters

        args = dict(
            strict_updates=True
        )
        p = Parameters(params=args)
        assert p.strict_updates == 'enabled'

        args = dict(
            strict_updates=False
        )
        p = Parameters(params=args)
        assert p.strict_updates == 'disabled'

    def test_module_strict_updates_override_from_top_level(self):
        args = dict(
            strict_updates=True,
            parameters=dict(
                strictUpdates='disabled'
            )
        )
        p = Parameters(params=args)
        assert p.strict_updates == 'enabled'

        args = dict(
            strict_updates=False,
            parameters=dict(
                strictUpdates='enabled'
            )
        )
        p = Parameters(params=args)
        assert p.strict_updates == 'disabled'

    def test_module_strict_updates_only_parameters(self):
        args = dict(
            parameters=dict(
                strictUpdates='disabled'
            )
        )
        p = Parameters(params=args)
        assert p.strict_updates == 'disabled'

        args = dict(
            parameters=dict(
                strictUpdates='enabled'
            )
        )
        p = Parameters(params=args)
        assert p.strict_updates == 'enabled'

    def test_api_strict_updates_from_top_level(self):
        args = dict(
            strictUpdates='enabled'
        )
        p = Parameters(params=args)
        assert p.strict_updates == 'enabled'

        args = dict(
            strictUpdates='disabled'
        )
        p = Parameters(params=args)
        assert p.strict_updates == 'disabled'

    def test_api_parameters_variables(self):
        args = dict(
            variables=[
                dict(
                    name="client__http_compression",
                    encrypted="no",
                    value="/#create_new#"
                )
            ]
        )
        p = Parameters(params=args)
        assert p.variables[0]['name'] == 'client__http_compression'

    def test_api_parameters_tables(self):
        args = dict(
            tables=[
                {
                    "name": "pool__members",
                    "columnNames": [
                        "addr",
                        "port",
                        "connection_limit"
                    ],
                    "rows": [
                        {
                            "row": [
                                "12.12.12.12",
                                "80",
                                "0"
                            ]
                        },
                        {
                            "row": [
                                "13.13.13.13",
                                "443",
                                10
                            ]
                        }
                    ]
                }
            ]
        )
        p = Parameters(params=args)
        assert p.tables[0]['name'] == 'pool__members'
        assert p.tables[0]['columnNames'] == ['addr', 'port', 'connection_limit']
        assert len(p.tables[0]['rows']) == 2
        assert 'row' in p.tables[0]['rows'][0]
        assert 'row' in p.tables[0]['rows'][1]
        assert p.tables[0]['rows'][0]['row'] == ['12.12.12.12', '80', '0']
        assert p.tables[0]['rows'][1]['row'] == ['13.13.13.13', '443', '10']

    def test_api_parameters_device_group(self):
        args = dict(
            deviceGroup='none'
        )
        p = Parameters(params=args)
        assert p.deviceGroup == 'none'

    def test_api_parameters_inherited_traffic_group(self):
        args = dict(
            inheritedTrafficGroup='true'
        )
        p = Parameters(params=args)
        assert p.inheritedTrafficGroup == 'true'

    def test_api_parameters_inherited_devicegroup(self):
        args = dict(
            inheritedDevicegroup='true'
        )
        p = Parameters(params=args)
        assert p.inheritedDevicegroup == 'true'

    def test_api_parameters_traffic_group(self):
        args = dict(
            trafficGroup='/Common/traffic-group-local-only'
        )
        p = Parameters(params=args)
        assert p.traffic_group == '/Common/traffic-group-local-only'

    def test_module_template_same_partition(self):
        args = dict(
            template='foo',
            partition='bar'
        )
        p = Parameters(params=args)
        assert p.template == '/bar/foo'

    def test_module_template_same_partition_full_path(self):
        args = dict(
            template='/bar/foo',
            partition='bar'
        )
        p = Parameters(params=args)
        assert p.template == '/bar/foo'

    def test_module_template_different_partition_full_path(self):
        args = dict(
            template='/Common/foo',
            partition='bar'
        )
        p = Parameters(params=args)
        assert p.template == '/Common/foo'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_service(self, *args):
        parameters = load_fixture('create_iapp_service_parameters_f5_http.json')
        set_module_args(dict(
            name='foo',
            template='f5.http',
            parameters=parameters,
            state='present',
            password='passsword',
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

    def test_update_agent_status_traps(self, *args):
        parameters = load_fixture('update_iapp_service_parameters_f5_http.json')
        set_module_args(dict(
            name='foo',
            template='f5.http',
            parameters=parameters,
            state='present',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        parameters = load_fixture('create_iapp_service_parameters_f5_http.json')
        current = Parameters(parameters)

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()
        assert results['changed'] is True

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
    from library.modules.bigip_snmp import ApiParameters
    from library.modules.bigip_snmp import ModuleParameters
    from library.modules.bigip_snmp import ModuleManager
    from library.modules.bigip_snmp import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_snmp import ApiParameters
        from ansible.modules.network.f5.bigip_snmp import ModuleParameters
        from ansible.modules.network.f5.bigip_snmp import ModuleManager
        from ansible.modules.network.f5.bigip_snmp import ArgumentSpec
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
            agent_status_traps='enabled',
            agent_authentication_traps='enabled',
            contact='Alice@foo.org',
            device_warning_traps='enabled',
            location='Lunar orbit',
            password='password',
            server='localhost',
            user='admin'
        )
        p = ModuleParameters(params=args)
        assert p.agent_status_traps == 'enabled'
        assert p.agent_authentication_traps == 'enabled'
        assert p.device_warning_traps == 'enabled'
        assert p.location == 'Lunar orbit'
        assert p.contact == 'Alice@foo.org'

    def test_module_parameters_disabled(self):
        args = dict(
            agent_status_traps='disabled',
            agent_authentication_traps='disabled',
            device_warning_traps='disabled',
            password='password',
            server='localhost',
            user='admin'
        )
        p = ModuleParameters(params=args)
        assert p.agent_status_traps == 'disabled'
        assert p.agent_authentication_traps == 'disabled'
        assert p.device_warning_traps == 'disabled'

    def test_api_parameters(self):
        args = dict(
            agentTrap='enabled',
            authTrap='enabled',
            bigipTraps='enabled',
            sysLocation='Lunar orbit',
            sysContact='Alice@foo.org',
        )
        p = ApiParameters(params=args)
        assert p.agent_status_traps == 'enabled'
        assert p.agent_authentication_traps == 'enabled'
        assert p.device_warning_traps == 'enabled'
        assert p.location == 'Lunar orbit'
        assert p.contact == 'Alice@foo.org'

    def test_api_parameters_disabled(self):
        args = dict(
            agentTrap='disabled',
            authTrap='disabled',
            bigipTraps='disabled',
        )
        p = ApiParameters(params=args)
        assert p.agent_status_traps == 'disabled'
        assert p.agent_authentication_traps == 'disabled'
        assert p.device_warning_traps == 'disabled'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update_agent_status_traps(self, *args):
        set_module_args(dict(
            agent_status_traps='enabled',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(
            params=dict(
                agent_status_traps='disabled'
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['agent_status_traps'] == 'enabled'

    def test_update_allowed_addresses(self, *args):
        set_module_args(dict(
            allowed_addresses=[
                '127.0.0.0/8',
                '10.10.10.10',
                'foo',
                'baz.foo.com'
            ],
            password='passsword',
            server='localhost',
            user='admin'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(
            params=dict(
                allowed_addresses=['127.0.0.0/8']
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert len(results['allowed_addresses']) == 4
        assert results['allowed_addresses'] == [
            '10.10.10.10', '127.0.0.0/8', 'baz.foo.com', 'foo'
        ]

    def test_update_allowed_addresses_default(self, *args):
        set_module_args(dict(
            allowed_addresses=[
                'default'
            ],
            password='passsword',
            server='localhost',
            user='admin'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(
            params=dict(
                allowed_addresses=['10.0.0.0']
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert len(results['allowed_addresses']) == 1
        assert results['allowed_addresses'] == ['127.0.0.0/8']

    def test_update_allowed_addresses_empty(self, *args):
        set_module_args(dict(
            allowed_addresses=[''],
            password='passsword',
            server='localhost',
            user='admin'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(
            params=dict(
                allowed_addresses=['10.0.0.0']
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert len(results['allowed_addresses']) == 1
        assert results['allowed_addresses'] == ['127.0.0.0/8']

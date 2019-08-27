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
    from library.modules.bigip_device_ntp import Parameters
    from library.modules.bigip_device_ntp import ModuleManager
    from library.modules.bigip_device_ntp import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_device_ntp import Parameters
    from ansible.modules.network.f5.bigip_device_ntp import ModuleManager
    from ansible.modules.network.f5.bigip_device_ntp import ArgumentSpec

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
        ntp = ['192.168.1.1', '192.168.1.2']
        args = dict(
            ntp_servers=ntp,
            timezone='Arctic/Longyearbyen'
        )

        p = Parameters(params=args)
        assert p.ntp_servers == ntp
        assert p.timezone == 'Arctic/Longyearbyen'

    def test_api_parameters(self):
        ntp = ['192.168.1.1', '192.168.1.2']
        args = dict(
            servers=ntp,
            timezone='Arctic/Longyearbyen'
        )

        p = Parameters(params=args)
        assert p.ntp_servers == ntp
        assert p.timezone == 'Arctic/Longyearbyen'


class TestModuleManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update_ntp_servers(self, *args):
        ntp = ['10.1.1.1', '10.1.1.2']
        set_module_args(
            dict(
                ntp_servers=ntp,
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(params=load_fixture('load_ntp.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['ntp_servers'] == ntp

    def test_update_timezone(self, *args):
        set_module_args(
            dict(
                timezone='Arctic/Longyearbyen',
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(params=load_fixture('load_ntp.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['timezone'] == 'Arctic/Longyearbyen'

    def test_update_ntp_servers_and_timezone(self, *args):
        ntp = ['10.1.1.1', '10.1.1.2']
        set_module_args(
            dict(
                ntp_servers=ntp,
                timezone='Arctic/Longyearbyen',
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(params=load_fixture('load_ntp.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['ntp_servers'] == ntp
        assert results['timezone'] == 'Arctic/Longyearbyen'

    def test_absent_ntp_servers(self, *args):
        ntp = []
        set_module_args(
            dict(
                ntp_servers=ntp,
                timezone='America/Los_Angeles',
                state='absent',
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(params=load_fixture('load_ntp.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.absent_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['ntp_servers'] == ntp
        assert not hasattr(results, 'timezone')

    def test_absent_timezone(self, *args):
        set_module_args(
            dict(
                timezone='',
                state='absent',
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(params=load_fixture('load_ntp.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.absent_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()
        assert results['changed'] is False

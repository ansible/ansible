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

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import F5ModuleError

try:
    from library.bigip_device_connectivity import Parameters
    from library.bigip_device_connectivity import ModuleManager
    from library.bigip_device_connectivity import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_device_connectivity import Parameters
        from ansible.modules.network.f5.bigip_device_connectivity import ModuleManager
        from ansible.modules.network.f5.bigip_device_connectivity import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


def load_fixture(name):
    path = os.path.join(fixture_path, name)
    with open(path) as f:
        data = f.read()
    try:
        data = json.loads(data)
    except Exception:
        pass
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            multicast_port='1010',
            multicast_address='10.10.10.10',
            multicast_interface='eth0',
            failover_multicast=True,
            unicast_failover=[
                dict(
                    address='20.20.20.20',
                    port='1234'
                )
            ],
            mirror_primary_address='1.2.3.4',
            mirror_secondary_address='5.6.7.8',
            config_sync_ip='4.3.2.1',
            state='present',
            server='localhost',
            user='admin',
            password='password'
        )
        p = Parameters(args)
        assert p.multicast_port == 1010
        assert p.multicast_address == '10.10.10.10'
        assert p.multicast_interface == 'eth0'
        assert p.failover_multicast is True
        assert p.mirror_primary_address == '1.2.3.4'
        assert p.mirror_secondary_address == '5.6.7.8'
        assert p.config_sync_ip == '4.3.2.1'
        assert len(p.unicast_failover) == 1
        assert 'effectiveIp' in p.unicast_failover[0]
        assert 'effectivePort' in p.unicast_failover[0]
        assert 'port' in p.unicast_failover[0]
        assert 'ip' in p.unicast_failover[0]
        assert p.unicast_failover[0]['effectiveIp'] == '20.20.20.20'
        assert p.unicast_failover[0]['ip'] == '20.20.20.20'
        assert p.unicast_failover[0]['port'] == 1234
        assert p.unicast_failover[0]['effectivePort'] == 1234

    def test_api_parameters(self):
        params = load_fixture('load_tm_cm_device.json')
        p = Parameters(params)
        assert p.multicast_port == 62960
        assert p.multicast_address == '224.0.0.245'
        assert p.multicast_interface == 'eth0'
        assert p.mirror_primary_address == '10.2.2.2'
        assert p.mirror_secondary_address == '10.2.3.2'
        assert p.config_sync_ip == '10.2.2.2'
        assert len(p.unicast_failover) == 2
        assert 'effectiveIp' in p.unicast_failover[0]
        assert 'effectivePort' in p.unicast_failover[0]
        assert 'port' in p.unicast_failover[0]
        assert 'ip' in p.unicast_failover[0]
        assert p.unicast_failover[0]['effectiveIp'] == 'management-ip'
        assert p.unicast_failover[0]['ip'] == 'management-ip'
        assert p.unicast_failover[0]['port'] == 1026
        assert p.unicast_failover[0]['effectivePort'] == 1026


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update_settings(self, *args):
        set_module_args(dict(
            config_sync_ip="10.1.30.1",
            mirror_primary_address="10.1.30.1",
            unicast_failover=[
                dict(
                    address="10.1.30.1"
                )
            ],
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(load_fixture('load_tm_cm_device_default.json'))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['config_sync_ip'] == '10.1.30.1'
        assert results['mirror_primary_address'] == '10.1.30.1'
        assert len(results.keys()) == 3

    def test_set_primary_mirror_address_none(self, *args):
        set_module_args(dict(
            mirror_primary_address="none",
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(load_fixture('load_tm_cm_device.json'))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['mirror_primary_address'] == 'none'
        assert len(results.keys()) == 2

    def test_set_secondary_mirror_address_none(self, *args):
        set_module_args(dict(
            mirror_secondary_address="none",
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(load_fixture('load_tm_cm_device.json'))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['mirror_secondary_address'] == 'none'
        assert len(results.keys()) == 2

    def test_set_multicast_address_none(self, *args):
        set_module_args(dict(
            multicast_address="none",
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(load_fixture('load_tm_cm_device.json'))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['multicast_address'] == 'none'
        assert len(results.keys()) == 2

    def test_set_multicast_port_negative(self, *args):
        set_module_args(dict(
            multicast_port=-1,
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(load_fixture('load_tm_cm_device.json'))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()

        assert 'must be between' in str(ex)

    def test_set_multicast_address(self, *args):
        set_module_args(dict(
            multicast_address="10.1.1.1",
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(load_fixture('load_tm_cm_device.json'))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['multicast_address'] == '10.1.1.1'
        assert len(results.keys()) == 2

    def test_unset_unicast_failover(self, *args):
        set_module_args(dict(
            unicast_failover="none",
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(load_fixture('load_tm_cm_device.json'))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['unicast_failover'] == 'none'
        assert len(results.keys()) == 2

    def test_unset_config_sync_ip(self, *args):
        set_module_args(dict(
            config_sync_ip="none",
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(load_fixture('load_tm_cm_device.json'))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['config_sync_ip'] == 'none'
        assert len(results.keys()) == 2

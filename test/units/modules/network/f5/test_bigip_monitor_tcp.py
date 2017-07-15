# -*- coding: utf-8 -*-
#
# Copyright 2017 F5 Networks Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public Liccense for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys
import pytest

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
    from library.bigip_monitor_tcp import ParametersTcp
    from library.bigip_monitor_tcp import ParametersHalfOpen
    from library.bigip_monitor_tcp import ParametersEcho
    from library.bigip_monitor_tcp import ModuleManager
    from library.bigip_monitor_tcp import ArgumentSpec
    from library.bigip_monitor_tcp import TcpManager
    from library.bigip_monitor_tcp import TcpEchoManager
    from library.bigip_monitor_tcp import TcpHalfOpenManager
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_monitor_tcp import ParametersTcp
        from ansible.modules.network.f5.bigip_monitor_tcp import ParametersHalfOpen
        from ansible.modules.network.f5.bigip_monitor_tcp import ParametersEcho
        from ansible.modules.network.f5.bigip_monitor_tcp import ModuleManager
        from ansible.modules.network.f5.bigip_monitor_tcp import ArgumentSpec
        from ansible.modules.network.f5.bigip_monitor_tcp import TcpManager
        from ansible.modules.network.f5.bigip_monitor_tcp import TcpEchoManager
        from ansible.modules.network.f5.bigip_monitor_tcp import TcpHalfOpenManager
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
            parent='parent',
            send='this is a send string',
            receive='this is a receive string',
            ip='10.10.10.10',
            type='TTYPE_TCP',
            port=80,
            interval=20,
            timeout=30,
            time_until_up=60,
            partition='Common'
        )

        p = ParametersTcp(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.send == 'this is a send string'
        assert p.receive == 'this is a receive string'
        assert p.ip == '10.10.10.10'
        assert p.type == 'tcp'
        assert p.port == 80
        assert p.destination == '10.10.10.10:80'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60

    def test_module_parameters_ints_as_strings(self):
        args = dict(
            name='foo',
            parent='parent',
            send='this is a send string',
            receive='this is a receive string',
            ip='10.10.10.10',
            type='TTYPE_TCP',
            port='80',
            interval='20',
            timeout='30',
            time_until_up='60',
            partition='Common'
        )

        p = ParametersTcp(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.send == 'this is a send string'
        assert p.receive == 'this is a receive string'
        assert p.ip == '10.10.10.10'
        assert p.type == 'tcp'
        assert p.port == 80
        assert p.destination == '10.10.10.10:80'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60

    def test_api_parameters(self):
        args = dict(
            name='foo',
            defaultsFrom='/Common/parent',
            send='this is a send string',
            recv='this is a receive string',
            destination='10.10.10.10:80',
            interval=20,
            timeout=30,
            timeUntilUp=60
        )

        p = ParametersTcp(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.send == 'this is a send string'
        assert p.receive == 'this is a receive string'
        assert p.ip == '10.10.10.10'
        assert p.type == 'tcp'
        assert p.port == 80
        assert p.destination == '10.10.10.10:80'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_monitor(self, *args):
        set_module_args(dict(
            name='foo',
            parent='parent',
            send='this is a send string',
            receive='this is a receive string',
            ip='10.10.10.10',
            port=80,
            interval=20,
            timeout=30,
            time_until_up=60,
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['parent'] == '/Common/parent'

    def test_create_monitor_idempotent(self, *args):
        set_module_args(dict(
            name='foo',
            parent='tcp',
            send='this is a send string',
            receive='this is a receive string',
            ip='10.10.10.10',
            port=80,
            interval=20,
            timeout=30,
            time_until_up=60,
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_update_port(self, *args):
        set_module_args(dict(
            name='foo',
            port=800,
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['port'] == 800

    def test_update_interval(self, *args):
        set_module_args(dict(
            name='foo',
            interval=10,
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['interval'] == 10

    def test_update_interval_larger_than_existing_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            interval=30,
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()

        assert "must be less than" in str(ex)

    def test_update_interval_larger_than_new_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            interval=10,
            timeout=5,
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()

        assert "must be less than" in str(ex)

    def test_update_send(self, *args):
        set_module_args(dict(
            name='foo',
            send='this is another send string',
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['send'] == 'this is another send string'

    def test_update_receive(self, *args):
        set_module_args(dict(
            name='foo',
            receive='this is another receive string',
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['receive'] == 'this is another receive string'

    def test_update_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            timeout=300,
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['timeout'] == 300

    def test_update_time_until_up(self, *args):
        set_module_args(dict(
            name='foo',
            time_until_up=300,
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersTcp(load_fixture('load_ltm_monitor_tcp.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['time_until_up'] == 300


class TestParametersEcho(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            name='foo',
            parent='parent',
            ip='10.10.10.10',
            type='TTYPE_TCP_ECHO',
            interval=20,
            timeout=30,
            time_until_up=60,
            partition='Common'
        )

        p = ParametersEcho(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.ip == '10.10.10.10'
        assert p.type == 'tcp_echo'
        assert p.destination == '10.10.10.10'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60

    def test_module_parameters_ints_as_strings(self):
        args = dict(
            name='foo',
            parent='parent',
            ip='10.10.10.10',
            type='TTYPE_TCP_ECHO',
            interval='20',
            timeout='30',
            time_until_up='60',
            partition='Common'
        )

        p = ParametersEcho(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.ip == '10.10.10.10'
        assert p.type == 'tcp_echo'
        assert p.destination == '10.10.10.10'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60

    def test_api_parameters(self):
        args = dict(
            name='foo',
            defaultsFrom='/Common/parent',
            destination='10.10.10.10',
            interval=20,
            timeout=30,
            timeUntilUp=60
        )

        p = ParametersEcho(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.ip == '10.10.10.10'
        assert p.type == 'tcp_echo'
        assert p.destination == '10.10.10.10'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManagerEcho(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_monitor(self, *args):
        set_module_args(dict(
            name='foo',
            ip='10.10.10.10',
            interval=20,
            timeout=30,
            time_until_up=60,
            type='TTYPE_TCP_ECHO',
            parent_partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpEchoManager(client)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['parent'] == '/Common/tcp_echo'

    def test_create_monitor_idempotent(self, *args):
        set_module_args(dict(
            name='foo',
            ip='10.10.10.10',
            interval=20,
            timeout=30,
            time_until_up=60,
            type='TTYPE_TCP_ECHO',
            parent_partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersEcho(load_fixture('load_ltm_monitor_tcp_echo.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpEchoManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_update_interval(self, *args):
        set_module_args(dict(
            name='foo',
            interval=10,
            parent_partition='Common',
            type='TTYPE_TCP_ECHO',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersEcho(load_fixture('load_ltm_monitor_tcp_echo.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpEchoManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['interval'] == 10

    def test_update_interval_larger_than_existing_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            interval=30,
            parent_partition='Common',
            type='TTYPE_TCP_ECHO',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersEcho(load_fixture('load_ltm_monitor_tcp_echo.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpEchoManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()

        assert "must be less than" in str(ex)

    def test_update_interval_larger_than_new_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            interval=10,
            timeout=5,
            parent_partition='Common',
            type='TTYPE_TCP_ECHO',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersEcho(load_fixture('load_ltm_monitor_tcp_echo.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpEchoManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()

        assert "must be less than" in str(ex)

    def test_update_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            timeout=300,
            parent_partition='Common',
            type='TTYPE_TCP_ECHO',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersEcho(load_fixture('load_ltm_monitor_tcp_echo.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpEchoManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['timeout'] == 300

    def test_update_time_until_up(self, *args):
        set_module_args(dict(
            name='foo',
            time_until_up=300,
            parent_partition='Common',
            type='TTYPE_TCP_ECHO',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersEcho(load_fixture('load_ltm_monitor_tcp_echo.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpEchoManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['time_until_up'] == 300


class TestParametersHalfOpen(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            name='foo',
            parent='parent',
            ip='10.10.10.10',
            port=80,
            type='TTYPE_TCP_HALF_OPEN',
            interval=20,
            timeout=30,
            time_until_up=60,
            partition='Common'
        )

        p = ParametersHalfOpen(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.ip == '10.10.10.10'
        assert p.port == 80
        assert p.type == 'tcp_half_open'
        assert p.destination == '10.10.10.10:80'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60

    def test_module_parameters_ints_as_strings(self):
        args = dict(
            name='foo',
            parent='parent',
            ip='10.10.10.10',
            port=80,
            type='TTYPE_TCP_HALF_OPEN',
            interval='20',
            timeout='30',
            time_until_up='60',
            partition='Common'
        )

        p = ParametersHalfOpen(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.ip == '10.10.10.10'
        assert p.port == 80
        assert p.type == 'tcp_half_open'
        assert p.destination == '10.10.10.10:80'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60

    def test_api_parameters(self):
        args = dict(
            name='foo',
            defaultsFrom='/Common/parent',
            destination='10.10.10.10:80',
            interval=20,
            timeout=30,
            timeUntilUp=60
        )

        p = ParametersHalfOpen(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/parent'
        assert p.ip == '10.10.10.10'
        assert p.port == 80
        assert p.type == 'tcp_half_open'
        assert p.destination == '10.10.10.10:80'
        assert p.interval == 20
        assert p.timeout == 30
        assert p.time_until_up == 60


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManagerHalfOpen(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_monitor(self, *args):
        set_module_args(dict(
            name='foo',
            ip='10.10.10.10',
            port=80,
            interval=20,
            timeout=30,
            time_until_up=60,
            type='TTYPE_TCP_HALF_OPEN',
            parent_partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpHalfOpenManager(client)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['parent'] == '/Common/tcp_half_open'

    def test_create_monitor_idempotent(self, *args):
        set_module_args(dict(
            name='foo',
            ip='10.10.10.10',
            port=80,
            interval=20,
            timeout=30,
            time_until_up=60,
            type='TTYPE_TCP_HALF_OPEN',
            parent_partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersHalfOpen(load_fixture('load_ltm_monitor_tcp_half_open.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpHalfOpenManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_update_interval(self, *args):
        set_module_args(dict(
            name='foo',
            interval=10,
            parent_partition='Common',
            type='TTYPE_TCP_HALF_OPEN',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersHalfOpen(load_fixture('load_ltm_monitor_tcp_half_open.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpHalfOpenManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['interval'] == 10

    def test_update_interval_larger_than_existing_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            interval=30,
            parent_partition='Common',
            type='TTYPE_TCP_HALF_OPEN',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersHalfOpen(load_fixture('load_ltm_monitor_tcp_half_open.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpHalfOpenManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()

        assert "must be less than" in str(ex)

    def test_update_interval_larger_than_new_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            interval=10,
            timeout=5,
            parent_partition='Common',
            type='TTYPE_TCP_HALF_OPEN',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersHalfOpen(load_fixture('load_ltm_monitor_tcp_half_open.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpHalfOpenManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()

        assert "must be less than" in str(ex)

    def test_update_timeout(self, *args):
        set_module_args(dict(
            name='foo',
            timeout=300,
            parent_partition='Common',
            type='TTYPE_TCP_HALF_OPEN',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersHalfOpen(load_fixture('load_ltm_monitor_tcp_half_open.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpHalfOpenManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['timeout'] == 300

    def test_update_time_until_up(self, *args):
        set_module_args(dict(
            name='foo',
            time_until_up=300,
            parent_partition='Common',
            type='TTYPE_TCP_HALF_OPEN',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ParametersHalfOpen(load_fixture('load_ltm_monitor_tcp_half_open.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TcpHalfOpenManager(client)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['time_until_up'] == 300

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
    from library.bigip_pool import Parameters
    from library.bigip_pool import ModuleManager
    from library.bigip_pool import ArgumentSpec
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_pool import Parameters
        from ansible.modules.network.f5.bigip_pool import ModuleManager
        from ansible.modules.network.f5.bigip_pool import ArgumentSpec
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


class BigIpObj(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        m = ['/Common/Fake', '/Common/Fake2']
        args = dict(
            monitor_type='m_of_n',
            monitors=m,
            quorum=1,
            slow_ramp_time=200,
            reselect_tries=5,
            service_down_action='drop',
            host='192.168.1.1',
            port=8080
        )

        p = Parameters(args)
        assert p.monitor_type == 'm_of_n'
        assert p.quorum == 1
        assert p.monitors == m
        assert p.monitor == 'min 1 of { /Common/Fake /Common/Fake2 }'
        assert p.host == '192.168.1.1'
        assert p.port == 8080
        assert p.member_name == '192.168.1.1:8080'
        assert p.slow_ramp_time == 200
        assert p.reselect_tries == 5
        assert p.service_down_action == 'drop'

    def test_api_parameters(self):
        m = ['/Common/Fake', '/Common/Fake2']
        args = dict(
            monitor_type='and_list',
            monitors=m,
            slowRampTime=200,
            reselectTries=5,
            serviceDownAction='drop'
        )

        p = Parameters(args)
        assert p.monitor == '/Common/Fake and /Common/Fake2'
        assert p.slow_ramp_time == 200
        assert p.reselect_tries == 5
        assert p.service_down_action == 'drop'

    def test_unknown_module_lb_method(self):
        args = dict(
            lb_method='obscure_hyphenated_fake_method',
        )
        with pytest.raises(F5ModuleError):
            p = Parameters(args)
            assert p.lb_method == 'foo'

    def test_unknown_api_lb_method(self):
        args = dict(
            loadBalancingMode='obscure_hypenated_fake_method'
        )
        with pytest.raises(F5ModuleError):
            p = Parameters(args)
            assert p.lb_method == 'foo'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.loaded_members = []
        members = load_fixture('pool_members_subcollection.json')
        for item in members:
            self.loaded_members.append(BigIpObj(**item))

    def test_create_pool(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            description='fakepool',
            service_down_action='drop',
            lb_method='round_robin',
            partition='Common',
            slow_ramp_time=10,
            reselect_tries=1,
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = lambda: True
        mm.exists = lambda: False

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_pool'
        assert results['description'] == 'fakepool'
        assert results['service_down_action'] == 'drop'
        assert results['lb_method'] == 'round-robin'
        assert results['slow_ramp_time'] == 10
        assert results['reselect_tries'] == 1

    def test_create_pool_with_pool_member(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            partition='Common',
            host='192.168.1.1',
            port=8080,
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        current = (
            Parameters(
                load_fixture('load_ltm_pool.json')
            ),
            self.loaded_members,
            {},
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)
        mm.read_current_from_device = Mock(return_value=current)
        mm.create_member_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['host'] == '192.168.1.1'
        assert results['port'] == 8080
        assert results['member_name'] == '192.168.1.1:8080'

    def test_create_pool_invalid_host(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            partition='Common',
            host='this.will.fail',
            port=8080,
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        msg = "'this.will.fail' is not a valid IP address"

        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()
        assert str(err.value) == msg

    def test_create_pool_invalid_port(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            partition='Common',
            host='192.168.1.1',
            port=98741,
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        msg = "The provided port '98741' must be between 0 and 65535"

        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()
        assert str(err.value) == msg

    def test_create_pool_monitor_type_missing(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            lb_method='round_robin',
            partition='Common',
            monitors=['/Common/tcp', '/Common/http'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        msg = "The 'monitor_type' parameter cannot be empty when " \
              "'monitors' parameter is specified."
        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()

        assert str(err.value) == msg

    def test_create_pool_monitors_missing(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            lb_method='round_robin',
            partition='Common',
            monitor_type='and_list',
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        msg = "The 'monitor' parameter cannot be empty when " \
              "'monitor_type' parameter is specified"
        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()

        assert str(err.value) == msg

    def test_create_pool_quorum_missing(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            lb_method='round_robin',
            partition='Common',
            monitor_type='m_of_n',
            monitors=['/Common/tcp', '/Common/http'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        msg = "Quorum value must be specified with monitor_type 'm_of_n'."
        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()

        assert str(err.value) == msg

    def test_create_pool_monitor_and_list(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            partition='Common',
            monitor_type='and_list',
            monitors=['/Common/tcp', '/Common/http'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_pool'
        assert results['monitors'] == ['/Common/tcp', '/Common/http']
        assert results['monitor_type'] == 'and_list'
        assert results['monitor'] == '/Common/tcp and /Common/http'

    def test_create_pool_monitor_m_of_n(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            partition='Common',
            monitor_type='m_of_n',
            quorum=1,
            monitors=['/Common/tcp', '/Common/http'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_pool'
        assert results['monitors'] == ['/Common/tcp', '/Common/http']
        assert results['monitor_type'] == 'm_of_n'
        assert results['monitor'] == 'min 1 of { /Common/tcp /Common/http }'

    def test_update_monitors(self, *args):
        set_module_args(dict(
            name='test_pool',
            partition='Common',
            monitor_type='and_list',
            monitors=['/Common/http', '/Common/tcp'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        current = (
            Parameters(
                load_fixture('load_ltm_pool.json')
            ),
            [],
            {},
        )

        mm.update_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['monitors'] == ['/Common/http', '/Common/tcp']
        assert results['monitor_type'] == 'and_list'
        assert results['monitor'] == '/Common/http and /Common/tcp'

    def test_update_pool_new_member(self, *args):
        set_module_args(dict(
            name='test_pool',
            partition='Common',
            host='192.168.1.1',
            port=8080,
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        current = (
            Parameters(
                load_fixture('load_ltm_pool.json')
            ),
            self.loaded_members,
            {},
        )

        mm.update_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.create_member_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['host'] == '192.168.1.1'
        assert results['port'] == 8080

    def test_update_pool_member_exists(self, *args):
        set_module_args(dict(
            name='test_pool',
            partition='Common',
            host='1.1.1.1',
            port=80,
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        current = (
            Parameters(
                load_fixture('load_ltm_pool.json')
            ),
            self.loaded_members,
            {},
        )

        mm.update_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.create_member_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_create_pool_monitor_and_list_no_partition(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            monitor_type='and_list',
            monitors=['tcp', 'http'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_pool'
        assert results['monitors'] == ['/Common/tcp', '/Common/http']
        assert results['monitor_type'] == 'and_list'
        assert results['monitor'] == '/Common/tcp and /Common/http'

    def test_create_pool_monitor_m_of_n_no_partition(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            monitor_type='m_of_n',
            quorum=1,
            monitors=['tcp', 'http'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_pool'
        assert results['monitors'] == ['/Common/tcp', '/Common/http']
        assert results['monitor_type'] == 'm_of_n'
        assert results['monitor'] == 'min 1 of { /Common/tcp /Common/http }'

    def test_create_pool_monitor_and_list_custom_partition(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            partition='Testing',
            monitor_type='and_list',
            monitors=['tcp', 'http'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_pool'
        assert results['monitors'] == ['/Testing/tcp', '/Testing/http']
        assert results['monitor_type'] == 'and_list'
        assert results['monitor'] == '/Testing/tcp and /Testing/http'

    def test_create_pool_monitor_m_of_n_custom_partition(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            partition='Testing',
            monitor_type='m_of_n',
            quorum=1,
            monitors=['tcp', 'http'],
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        mm = ModuleManager(client)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_pool'
        assert results['monitors'] == ['/Testing/tcp', '/Testing/http']
        assert results['monitor_type'] == 'm_of_n'
        assert results['monitor'] == 'min 1 of { /Testing/tcp /Testing/http }'

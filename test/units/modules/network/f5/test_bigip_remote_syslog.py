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
    from library.modules.bigip_remote_syslog import Parameters
    from library.modules.bigip_remote_syslog import ModuleManager
    from library.modules.bigip_remote_syslog import ArgumentSpec
    from library.modules.bigip_remote_syslog import HAS_F5SDK
    from library.modules.bigip_remote_syslog import HAS_NETADDR
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_remote_syslog import Parameters
        from ansible.modules.network.f5.bigip_remote_syslog import ModuleManager
        from ansible.modules.network.f5.bigip_remote_syslog import ArgumentSpec
        from ansible.modules.network.f5.bigip_remote_syslog import HAS_F5SDK
        from ansible.modules.network.f5.bigip_remote_syslog import HAS_NETADDR
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

    from ansible.modules.network.f5.bigip_remote_syslog import HAS_NETADDR
    if not HAS_NETADDR:
        raise SkipTest("F5 Ansible modules require the netaddr Python library")

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
            remote_host='10.10.10.10',
            remote_port=514,
            local_ip='1.1.1.1'
        )

        p = Parameters(params=args)
        assert p.remote_host == '10.10.10.10'
        assert p.remote_port == 514
        assert p.local_ip == '1.1.1.1'

    def test_api_parameters(self):
        args = dict(
            remoteServers=[
                dict(
                    name='/Common/remotesyslog1',
                    host='10.10.10.10',
                    localIp='none',
                    remotePort=514
                )
            ]
        )

        p = Parameters(params=args)
        assert len(p.remoteServers) == 1


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_remote_syslog(self, *args):
        set_module_args(dict(
            remote_host='10.10.10.10',
            server='localhost',
            password='password',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(side_effect=[False, True])
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_remote_syslog_idempotent(self, *args):
        set_module_args(dict(
            remote_host='10.10.10.10',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = Parameters(params=load_fixture('load_tm_sys_syslog.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_update_remote_port(self, *args):
        set_module_args(dict(
            remote_host='10.10.10.10',
            remote_port=800,
            server='localhost',
            password='password',
            user='admin'
        ))

        current = Parameters(params=load_fixture('load_tm_sys_syslog.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['remote_port'] == 800

    def test_update_local_ip(self, *args):
        set_module_args(dict(
            remote_host='10.10.10.10',
            local_ip='2.2.2.2',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = Parameters(params=load_fixture('load_tm_sys_syslog.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['local_ip'] == '2.2.2.2'

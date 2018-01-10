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
from ansible.compat.tests.mock import patch
from ansible.compat.tests.mock import Mock
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_command import Parameters
    from library.bigip_command import ModuleManager
    from library.bigip_command import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_command import Parameters
        from ansible.modules.network.f5.bigip_command import ModuleManager
        from ansible.modules.network.f5.bigip_command import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


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
            commands=[
                "tmsh show sys version"
            ],
            server='localhost',
            user='admin',
            password='password'
        )
        p = Parameters(args)
        assert len(p.commands) == 2


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_run_single_command(self, *args):
        set_module_args(dict(
            commands=[
                "tmsh show sys version"
            ],
            server='localhost',
            user='admin',
            password='password'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)
        mm._run_commands = Mock(return_value=[])
        mm.execute_on_device = Mock(return_value=[])

        results = mm.exec_module()

        assert results['changed'] is False
        assert mm._run_commands.call_count == 0
        assert mm.execute_on_device.call_count == 1

    def test_run_single_modification_command(self, *args):
        set_module_args(dict(
            commands=[
                "tmsh create ltm virtual foo"
            ],
            server='localhost',
            user='admin',
            password='password'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)
        mm._run_commands = Mock(return_value=[])
        mm.execute_on_device = Mock(return_value=[])

        results = mm.exec_module()

        assert results['changed'] is True
        assert mm._run_commands.call_count == 0
        assert mm.execute_on_device.call_count == 1

    def test_cli_command(self, *args):
        set_module_args(dict(
            commands=[
                "show sys version"
            ],
            server='localhost',
            user='admin',
            password='password',
            transport='cli'
        ))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)
        mm._run_commands = Mock(return_value=[])
        mm.execute_on_device = Mock(return_value=[])

        results = mm.exec_module()

        assert results['changed'] is False
        assert mm._run_commands.call_count == 1
        assert mm.execute_on_device.call_count == 0

    def test_command_with_commas(self, *args):
        set_module_args(dict(
            commands="""
              tmsh create /auth ldap system-auth {bind-dn uid=binduser,
              cn=users,dc=domain,dc=com bind-pw $ENCRYPTEDPW check-roles-group
              enabled search-base-dn cn=users,dc=domain,dc=com servers add {
              ldap.server.com } }"
            """,
            server='localhost',
            user='admin',
            password='password'
        ))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)
        mm._run_commands = Mock(return_value=[])
        mm.execute_on_device = Mock(return_value=[])

        results = mm.exec_module()

        assert results['changed'] is True
        assert mm._run_commands.call_count == 0
        assert mm.execute_on_device.call_count == 1

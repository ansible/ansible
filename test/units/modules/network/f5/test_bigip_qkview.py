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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_qkview import Parameters
    from library.bigip_qkview import ModuleManager
    from library.bigip_qkview import MadmLocationManager
    from library.bigip_qkview import BulkLocationManager
    from library.bigip_qkview import ArgumentSpec
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_qkview import Parameters
        from ansible.modules.network.f5.bigip_qkview import ModuleManager
        from ansible.modules.network.f5.bigip_qkview import MadmLocationManager
        from ansible.modules.network.f5.bigip_qkview import BulkLocationManager
        from ansible.modules.network.f5.bigip_qkview import ArgumentSpec
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
            filename='foo.qkview',
            asm_request_log=False,
            max_file_size=1024,
            complete_information=True,
            exclude_core=True,
            force=False,
            exclude=['audit', 'secure'],
            dest='/tmp/foo.qkview'
        )
        p = Parameters(args)
        assert p.filename == 'foo.qkview'
        assert p.asm_request_log is None
        assert p.max_file_size == '-s 1024'
        assert p.complete_information == '-c'
        assert p.exclude_core == '-C'
        assert p.force is False
        assert len(p.exclude_core) == 2
        assert 'audit' in p.exclude
        assert 'secure' in p.exclude
        assert p.dest == '/tmp/foo.qkview'

    def test_module_asm_parameter(self):
        args = dict(
            asm_request_log=True,
        )
        p = Parameters(args)
        assert p.asm_request_log == '-o asm-request-log'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestMadmLocationManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_qkview_default_options(self, *args):
        set_module_args(dict(
            dest='/tmp/foo.qkview',
            server='localhost',
            user='admin',
            password='password'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = MadmLocationManager(client)
        tm.exists = Mock(return_value=False)
        tm.execute_on_device = Mock(return_value=True)
        tm._move_qkview_to_download = Mock(return_value=True)
        tm._download_file = Mock(return_value=True)
        tm._delete_qkview = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_less_than_14 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)

        with patch('os.path.exists') as mo:
            mo.return_value = True
            results = mm.exec_module()

        assert results['changed'] is False


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestBulkLocationManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_qkview_default_options(self, *args):
        set_module_args(dict(
            dest='/tmp/foo.qkview',
            server='localhost',
            user='admin',
            password='password'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = BulkLocationManager(client)
        tm.exists = Mock(return_value=False)
        tm.execute_on_device = Mock(return_value=True)
        tm._move_qkview_to_download = Mock(return_value=True)
        tm._download_file = Mock(return_value=True)
        tm._delete_qkview = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_less_than_14 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)

        with patch('os.path.exists') as mo:
            mo.return_value = True
            results = mm.exec_module()

        assert results['changed'] is False

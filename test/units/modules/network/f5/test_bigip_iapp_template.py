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
from ansible.module_utils import basic
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_iapp_template import Parameters
    from library.bigip_iapp_template import ModuleManager
    from library.bigip_iapp_template import ArgumentSpec
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_iapp_template import Parameters
        from ansible.modules.network.f5.bigip_iapp_template import ArgumentSpec
        from ansible.modules.network.f5.bigip_iapp_template import ModuleManager
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
        iapp = load_fixture('create_iapp_template.iapp')
        args = dict(
            content=iapp
        )
        p = Parameters(args)
        assert p.name == 'foo.iapp'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_iapp_template(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            content=load_fixture('basic-iapp.tmpl'),
            password='passsword',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_update_iapp_template(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            content=load_fixture('basic-iapp.tmpl'),
            password='passsword',
            server='localhost',
            user='admin'
        ))

        current1 = Parameters(load_fixture('load_sys_application_template_w_new_checksum.json'))
        current2 = Parameters(load_fixture('load_sys_application_template_w_old_checksum.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, True])
        mm.create_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current1)
        mm.template_in_use = Mock(return_value=False)
        mm._get_temporary_template = Mock(return_value=current2)
        mm._remove_iapp_checksum = Mock(return_value=None)
        mm._generate_template_checksum_on_device = Mock(return_value=None)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_delete_iapp_template(self, *args):
        set_module_args(dict(
            content=load_fixture('basic-iapp.tmpl'),
            password='passsword',
            server='localhost',
            user='admin',
            state='absent'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, False])
        mm.remove_from_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_delete_iapp_template_idempotent(self, *args):
        set_module_args(dict(
            content=load_fixture('basic-iapp.tmpl'),
            password='passsword',
            server='localhost',
            user='admin',
            state='absent'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, False])

        results = mm.exec_module()

        assert results['changed'] is False

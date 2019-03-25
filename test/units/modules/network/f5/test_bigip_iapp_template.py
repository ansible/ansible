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
    from library.modules.bigip_iapp_template import Parameters
    from library.modules.bigip_iapp_template import ModuleManager
    from library.modules.bigip_iapp_template import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_iapp_template import Parameters
    from ansible.modules.network.f5.bigip_iapp_template import ArgumentSpec
    from ansible.modules.network.f5.bigip_iapp_template import ModuleManager

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock
    from units.compat.mock import patch

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
        iapp = load_fixture('create_iapp_template.iapp')
        args = dict(
            content=iapp
        )
        p = Parameters(params=args)
        assert p.name == 'foo.iapp'

    def test_module_parameters_custom_name(self):
        iapp = load_fixture('create_iapp_template.iapp')
        args = dict(
            content=iapp,
            name='foobar'
        )
        p = Parameters(params=args)
        assert p.name == 'foobar'
        assert 'sys application template /Common/foobar' in p.content

    def test_module_parameters_custom_partition(self):
        iapp = load_fixture('create_iapp_template.iapp')
        args = dict(
            content=iapp,
            partition='foobar'
        )
        p = Parameters(params=args)
        assert p.name == 'foo.iapp'
        assert 'sys application template /foobar/foo.iapp' in p.content


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_iapp_template(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            content=load_fixture('basic-iapp.tmpl'),
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_update_iapp_template(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            content=load_fixture('basic-iapp.tmpl'),
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current1 = Parameters(params=load_fixture('load_sys_application_template_w_new_checksum.json'))
        current2 = Parameters(params=load_fixture('load_sys_application_template_w_old_checksum.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

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
            state='absent',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, False])
        mm.remove_from_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_delete_iapp_template_idempotent(self, *args):
        set_module_args(dict(
            content=load_fixture('basic-iapp.tmpl'),
            state='absent',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, False])

        results = mm.exec_module()

        assert results['changed'] is False

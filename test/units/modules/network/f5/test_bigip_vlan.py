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
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import F5ModuleError

try:
    from library.bigip_vlan import Parameters
    from library.bigip_vlan import ModuleManager
    from library.bigip_vlan import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_vlan import Parameters
        from ansible.modules.network.f5.bigip_vlan import ModuleManager
        from ansible.modules.network.f5.bigip_vlan import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
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


class BigIpObj(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestParameters(unittest.TestCase):

    def setUp(self):
        self.loaded_ifcs = []
        ifcs_json = load_fixture('load_net_interfaces.json')
        for item in ifcs_json:
            self.loaded_ifcs.append(BigIpObj(**item))

    def test_module_parameters(self):
        args = dict(
            name='somevlan',
            tag=213,
            description='fakevlan',
            untagged_interfaces=['1.1'],
        )
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs
            p = Parameters(args)

        assert p.name == 'somevlan'
        assert p.tag == 213
        assert p.description == 'fakevlan'
        assert p.untagged_interfaces == ['1.1']

    def test_api_parameters(self):
        args = dict(
            name='somevlan',
            description='fakevlan',
            tag=213,
            tagged_interfaces=['1.2']
        )

        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs
            p = Parameters(args)

        assert p.name == 'somevlan'
        assert p.tag == 213
        assert p.interfaces == [{'tagged': True, 'name': '1.2'}]
        assert p.description == 'fakevlan'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.loaded_ifcs = []
        self.loaded_vlan_ifc_tag = []
        self.loaded_vlan_ifc_untag = []
        ifcs_tag = load_fixture('load_vlan_tagged_ifcs.json')
        ifcs_untag = load_fixture('load_vlan_untag_ifcs.json')
        ifcs_json = load_fixture('load_net_interfaces.json')
        for item in ifcs_json:
            self.loaded_ifcs.append(BigIpObj(**item))
        for item in ifcs_tag:
            self.loaded_vlan_ifc_tag.append(BigIpObj(**item))
        for item in ifcs_untag:
            self.loaded_vlan_ifc_untag.append(BigIpObj(**item))

    def test_create_vlan(self, *args):
        set_module_args(dict(
            name='somevlan',
            description='fakevlan',
            server='localhost',
            password='password',
            user='admin',
            partition='Common'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs

            mm = ModuleManager(client)
            mm.create_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=False)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'somevlan'
        assert results['description'] == 'fakevlan'

    def test_create_vlan_tagged_interface(self, *args):
        set_module_args(dict(
            name='somevlan',
            tagged_interface=['2.1'],
            tag=213,
            server='localhost',
            password='password',
            user='admin',
            partition='Common'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs

            mm = ModuleManager(client)
            mm.create_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=False)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['interfaces'] == [{'tagged': True, 'name': '2.1'}]
        assert results['tag'] == 213
        assert results['name'] == 'somevlan'

    def test_create_vlan_untagged_interface(self, *args):
        set_module_args(dict(
            name='somevlan',
            untagged_interface=['2.1'],
            server='localhost',
            password='password',
            user='admin',
            partition='Common'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs

            mm = ModuleManager(client)
            mm.create_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=False)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['interfaces'] == [{'untagged': True, 'name': '2.1'}]
        assert results['name'] == 'somevlan'

    def test_create_vlan_tagged_interfaces(self, *args):
        set_module_args(dict(
            name='somevlan',
            tagged_interface=['2.1', '1.1'],
            tag=213,
            server='localhost',
            password='password',
            user='admin',
            partition='Common'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs

            mm = ModuleManager(client)
            mm.create_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=False)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['interfaces'] == [{'tagged': True, 'name': '2.1'},
                                         {'tagged': True, 'name': '1.1'}]
        assert results['tag'] == 213
        assert results['name'] == 'somevlan'

    def test_create_vlan_untagged_interfaces(self, *args):
        set_module_args(dict(
            name='somevlan',
            untagged_interface=['2.1', '1.1'],
            server='localhost',
            password='password',
            user='admin',
            partition='Common',
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs

            mm = ModuleManager(client)
            mm.create_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=False)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['interfaces'] == [{'untagged': True, 'name': '2.1'},
                                         {'untagged': True, 'name': '1.1'}]
        assert results['name'] == 'somevlan'

    def test_update_vlan_untag_interface(self, *args):
        set_module_args(dict(
            name='somevlan',
            untagged_interface=['2.1'],
            server='localhost',
            password='password',
            user='admin',
            partition='Common',
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        ifcs = self.loaded_vlan_ifc_untag
        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs
            mm = ModuleManager(client)

            current = (
                Parameters(
                    load_fixture('load_vlan.json')
                ),
                ifcs
            )

            mm.update_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=True)
            mm.read_current_from_device = Mock(return_value=current)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['interfaces'] == [{'untagged': True, 'name': '2.1'}]

    def test_update_vlan_tag_interface(self, *args):
        set_module_args(dict(
            name='somevlan',
            tagged_interface=['2.1'],
            server='localhost',
            password='password',
            user='admin',
            partition='Common',
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        ifcs = self.loaded_vlan_ifc_tag
        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs
            mm = ModuleManager(client)

            current = (
                Parameters(
                    load_fixture('load_vlan.json')
                ),
                ifcs
            )

            mm.update_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=True)
            mm.read_current_from_device = Mock(return_value=current)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['interfaces'] == [{'tagged': True, 'name': '2.1'}]

    def test_update_vlan_description(self, *args):
        set_module_args(dict(
            name='somevlan',
            description='changed_that',
            server='localhost',
            password='password',
            user='admin',
            partition='Common',
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        ifcs = self.loaded_vlan_ifc_tag
        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs
            mm = ModuleManager(client)

            current = (
                Parameters(
                    load_fixture('update_vlan_description.json')
                ),
                ifcs
            )

            mm.update_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=True)
            mm.read_current_from_device = Mock(return_value=current)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'changed_that'

    def test_untagged_ifc_raises(self, *args):
        set_module_args(dict(
            name='somevlan',
            untagged_interface=['10.2'],
            server='localhost',
            password='password',
            user='admin',
            partition='Common'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        msg = 'The specified interface "10.2" was not found'
        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs

            mm = ModuleManager(client)
            mm.create_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=False)

            with pytest.raises(F5ModuleError) as err:
                mm.exec_module()

        assert str(err.value) == msg

    def test_tagged_ifc_raises(self, *args):
        set_module_args(dict(
            name='somevlan',
            tagged_interface=['10.2'],
            tag=213,
            server='localhost',
            password='password',
            user='admin',
            partition='Common'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        msg = 'The specified interface "10.2" was not found'
        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = self.loaded_ifcs

            mm = ModuleManager(client)
            mm.create_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=False)

            with pytest.raises(F5ModuleError) as err:
                mm.exec_module()

        assert str(err.value) == msg

    def test_parse_return_ifcs_raises(self, *args):
        set_module_args(dict(
            name='somevlan',
            untagged_interface=['1.2'],
            server='localhost',
            password='password',
            user='admin',
            partition='Common'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        msg = 'No interfaces were found'
        # Override methods to force specific logic in the module to happen
        with patch.object(Parameters, '_get_interfaces_from_device') as obj:
            obj.return_value = []

            mm = ModuleManager(client)
            mm.create_on_device = Mock(return_value=True)
            mm.exists = Mock(return_value=False)

            with pytest.raises(F5ModuleError) as err:
                mm.exec_module()

        assert str(err.value) == msg

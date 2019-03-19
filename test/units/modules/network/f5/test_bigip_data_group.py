# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
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
    from library.modules.bigip_data_group import ModuleParameters
    from library.modules.bigip_data_group import ModuleManager
    from library.modules.bigip_data_group import ExternalManager
    from library.modules.bigip_data_group import InternalManager
    from library.modules.bigip_data_group import ArgumentSpec

    from library.module_utils.network.f5.common import F5ModuleError

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_data_group import ModuleParameters
    from ansible.modules.network.f5.bigip_data_group import ModuleManager
    from ansible.modules.network.f5.bigip_data_group import ExternalManager
    from ansible.modules.network.f5.bigip_data_group import InternalManager
    from ansible.modules.network.f5.bigip_data_group import ArgumentSpec

    from ansible.module_utils.network.f5.common import F5ModuleError

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
        args = dict(
            name='foo',
            type='address',
            delete_data_group_file=False,
            internal=False,
            records=[
                dict(
                    key='10.10.10.10/32',
                    value='bar'
                )
            ],
            separator=':=',
            state='present',
            partition='Common'
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.type == 'ip'
        assert p.delete_data_group_file is False
        assert len(p.records) == 1
        assert 'data' in p.records[0]
        assert 'name' in p.records[0]
        assert p.records[0]['data'] == 'bar'
        assert p.records[0]['name'] == '10.10.10.10/32'
        assert p.separator == ':='
        assert p.state == 'present'
        assert p.partition == 'Common'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_external_datagroup_type_string(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=False,
            records_src="{0}/data-group-string.txt".format(fixture_path),
            separator=':=',
            state='present',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = ExternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[False, True])
        mm1.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        results = mm0.exec_module()

        assert results['changed'] is True

    def test_create_external_incorrect_address_data(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=False,
            type='address',
            records_src="{0}/data-group-string.txt".format(fixture_path),
            separator=':=',
            state='present',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = ExternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[False, True])
        mm1.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        with pytest.raises(F5ModuleError) as ex:
            mm0.exec_module()

        assert "When specifying an 'address' type, the value to the left of the separator must be an IP." == str(ex.value)

    def test_create_external_incorrect_integer_data(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=False,
            type='integer',
            records_src="{0}/data-group-string.txt".format(fixture_path),
            separator=':=',
            state='present',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = ExternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[False, True])
        mm1.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        with pytest.raises(F5ModuleError) as ex:
            mm0.exec_module()

        assert "When specifying an 'integer' type, the value to the left of the separator must be a number." == str(ex.value)

    def test_remove_data_group_keep_file(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=False,
            state='absent',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = ExternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[True, False])
        mm1.remove_from_device = Mock(return_value=True)
        mm1.external_file_exists = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        results = mm0.exec_module()

        assert results['changed'] is True

    def test_remove_data_group_remove_file(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=True,
            internal=False,
            state='absent',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = ExternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[True, False])
        mm1.remove_from_device = Mock(return_value=True)
        mm1.external_file_exists = Mock(return_value=True)
        mm1.remove_data_group_file_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        results = mm0.exec_module()

        assert results['changed'] is True

    def test_create_internal_datagroup_type_string(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=True,
            records_src="{0}/data-group-string.txt".format(fixture_path),
            separator=':=',
            state='present',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = InternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[False, True])
        mm1.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        results = mm0.exec_module()

        assert results['changed'] is True

    def test_create_internal_incorrect_integer_data(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=True,
            type='integer',
            records_src="{0}/data-group-string.txt".format(fixture_path),
            separator=':=',
            state='present',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = InternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[False, True])
        mm1.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        with pytest.raises(F5ModuleError) as ex:
            mm0.exec_module()

        assert "When specifying an 'integer' type, the value to the left of the separator must be a number." == str(ex.value)

    def test_create_internal_datagroup_type_integer(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=True,
            type='integer',
            records_src="{0}/data-group-integer.txt".format(fixture_path),
            separator=':=',
            state='present',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = InternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[False, True])
        mm1.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        results = mm0.exec_module()

        assert results['changed'] is True

    def test_create_internal_datagroup_type_address(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=True,
            type='address',
            records_src="{0}/data-group-address.txt".format(fixture_path),
            separator=':=',
            state='present',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = InternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[False, True])
        mm1.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        results = mm0.exec_module()

        assert results['changed'] is True

    def test_create_internal_datagroup_type_address_list(self, *args):
        set_module_args(dict(
            name='foo',
            delete_data_group_file=False,
            internal=True,
            type='address',
            records=[
                dict(
                    key='10.0.0.0/8',
                    value='Network1'
                ),
                dict(
                    key='172.16.0.0/12',
                    value='Network2'
                ),
                dict(
                    key='192.168.20.1/16',
                    value='Network3'
                ),
                dict(
                    key='192.168.20.1',
                    value='Host1'
                ),
                dict(
                    key='172.16.1.1',
                    value='Host2'
                )
            ],
            separator=':=',
            state='present',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        mm1 = InternalManager(module=module, params=module.params)
        mm1.exists = Mock(side_effect=[False, True])
        mm1.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm0 = ModuleManager(module=module)
        mm0.get_manager = Mock(return_value=mm1)

        results = mm0.exec_module()

        assert results['changed'] is True

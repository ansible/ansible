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
    from library.modules.bigip_user import Parameters
    from library.modules.bigip_user import ModuleManager
    from library.modules.bigip_user import ArgumentSpec
    from library.modules.bigip_user import UnpartitionedManager
    from library.modules.bigip_user import PartitionedManager

    from library.module_utils.network.f5.common import F5ModuleError

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_user import Parameters
    from ansible.modules.network.f5.bigip_user import ModuleManager
    from ansible.modules.network.f5.bigip_user import ArgumentSpec
    from ansible.modules.network.f5.bigip_user import UnpartitionedManager
    from ansible.modules.network.f5.bigip_user import PartitionedManager

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
        access = [{'name': 'Common', 'role': 'guest'}]
        args = dict(
            username_credential='someuser',
            password_credential='testpass',
            full_name='Fake Person',
            partition_access=access,
            update_password='always'
        )

        p = Parameters(params=args)
        assert p.username_credential == 'someuser'
        assert p.password_credential == 'testpass'
        assert p.full_name == 'Fake Person'
        assert p.partition_access == access
        assert p.update_password == 'always'

    def test_api_parameters(self):
        access = [{'name': 'Common', 'role': 'guest'}]
        args = dict(
            name='someuser',
            description='Fake Person',
            partitionAccess=access,
            shell='none'
        )

        p = Parameters(params=args)
        assert p.name == 'someuser'
        assert p.full_name == 'Fake Person'
        assert p.partition_access == access
        assert p.shell == 'none'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_user(self, *args):
        access = [{'name': 'Common', 'role': 'guest'}]
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
            partition_access=access,
            update_password='on_create',
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

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.create_on_device = Mock(return_value=True)
        pm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['partition_access'] == access

    def test_create_user_no_password(self, *args):
        access = [{'name': 'Common', 'role': 'guest'}]
        set_module_args(dict(
            username_credential='someuser',
            partition_access=access,
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

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.create_on_device = Mock(return_value=True)
        pm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['partition_access'] == access

    def test_create_user_partition_access_raises(self, *args):
        set_module_args(dict(
            username_credential='someuser',
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

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.create_on_device = Mock(return_value=True)
        pm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        msg = "The 'partition_access' option " \
              "is required when creating a resource."

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()
        assert str(ex.value) == msg

    def test_create_user_shell_bash(self, *args):
        access = [{'name': 'all', 'role': 'admin'}]
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
            partition_access=access,
            update_password='on_create',
            shell='bash',
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

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.create_on_device = Mock(return_value=True)
        pm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['partition_access'] == access

    def test_create_user_shell_not_permitted_raises(self, *args):
        access = [{'name': 'Common', 'role': 'guest'}]
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
            partition_access=access,
            update_password='on_create',
            shell='bash',
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

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.create_on_device = Mock(return_value=True)
        pm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        msg = "Shell access is only available to 'admin' or " \
              "'resource-admin' roles."

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()
        assert str(ex.value) == msg

    def test_update_user_password_no_pass(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(params=load_fixture('load_auth_user_no_pass.json'))

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.exists = Mock(return_value=True)
        pm.update_on_device = Mock(return_value=True)
        pm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_update_user_password_with_pass(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(params=load_fixture('load_auth_user_with_pass.json'))

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.exists = Mock(return_value=True)
        pm.update_on_device = Mock(return_value=True)
        pm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_update_user_shell_to_none(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            shell='none',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(
            params=dict(
                user='admin',
                shell='tmsh'
            )
        )

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.exists = Mock(return_value=True)
        pm.update_on_device = Mock(return_value=True)
        pm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['shell'] == 'none'

    def test_update_user_shell_to_none_shell_attribute_missing(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            shell='none',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        access = [{'name': 'Common', 'role': 'guest'}]
        current = Parameters(
            params=dict(
                user='admin',
                partition_access=access
            )
        )

        # Override methods to force specific logic in the module to happen
        pm = PartitionedManager(module=module, params=module.params)
        pm.exists = Mock(return_value=True)
        pm.update_on_device = Mock(return_value=True)
        pm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=pm)

        results = mm.exec_module()

        assert results['changed'] is False
        assert not hasattr(results, 'shell')

    def test_update_user_shell_to_bash(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            shell='bash',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        access = [{'name': 'all', 'role': 'admin'}]
        current = Parameters(
            params=dict(
                user='admin',
                shell='tmsh',
                partition_access=access
            )
        )

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.exists = Mock(return_value=True)
        upm.update_on_device = Mock(return_value=True)
        upm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['shell'] == 'bash'

    def test_update_user_shell_to_bash_mutliple_roles(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            shell='bash',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        access = [
            {'name': 'Common', 'role': 'operator'},
            {'name': 'all', 'role': 'guest'}
        ]
        current = Parameters(
            params=dict(
                user='admin',
                shell='tmsh',
                partition_access=access
            )
        )

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.exists = Mock(return_value=True)
        upm.update_on_device = Mock(return_value=True)
        upm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        msg = "Shell access is only available to 'admin' or " \
              "'resource-admin' roles."

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()
        assert str(ex.value) == msg


class TestLegacyManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_user(self, *args):
        access = [{'name': 'Common', 'role': 'guest'}]
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
            partition_access=access,
            update_password='on_create',
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

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.create_on_device = Mock(return_value=True)
        upm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['partition_access'] == access

    def test_create_user_no_password(self, *args):
        access = [{'name': 'Common', 'role': 'guest'}]
        set_module_args(dict(
            username_credential='someuser',
            partition_access=access,
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

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.create_on_device = Mock(return_value=True)
        upm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['partition_access'] == access

    def test_create_user_partition_access_raises(self, *args):
        set_module_args(dict(
            username_credential='someuser',
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

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.create_on_device = Mock(return_value=True)
        upm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        msg = "The 'partition_access' option " \
              "is required when creating a resource."

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()
        assert str(ex.value) == msg

    def test_create_user_shell_bash(self, *args):
        access = [{'name': 'all', 'role': 'admin'}]
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
            partition_access=access,
            update_password='on_create',
            shell='bash',
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

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.create_on_device = Mock(return_value=True)
        upm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['partition_access'] == access

    def test_create_user_shell_not_permitted_raises(self, *args):
        access = [{'name': 'Common', 'role': 'guest'}]
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
            partition_access=access,
            update_password='on_create',
            shell='bash',
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

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.create_on_device = Mock(return_value=True)
        upm.exists = Mock(return_value=False)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        msg = "Shell access is only available to 'admin' or " \
              "'resource-admin' roles."

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()
        assert str(ex.value) == msg

    def test_update_user_password(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            password_credential='testpass',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        access = [{'name': 'Common', 'role': 'guest'}]
        current = Parameters(
            params=dict(
                shell='tmsh',
                partition_access=access
            )
        )

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.exists = Mock(return_value=True)
        upm.update_on_device = Mock(return_value=True)
        upm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_update_user_shell_to_none(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            shell='none',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(
            params=dict(
                user='admin',
                shell='tmsh'
            )
        )

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.exists = Mock(return_value=True)
        upm.update_on_device = Mock(return_value=True)
        upm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['shell'] == 'none'

    def test_update_user_shell_to_none_shell_attribute_missing(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            shell='none',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        access = [{'name': 'Common', 'role': 'guest'}]
        current = Parameters(
            params=dict(
                user='admin',
                partition_access=access
            )
        )

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.exists = Mock(return_value=True)
        upm.update_on_device = Mock(return_value=True)
        upm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        results = mm.exec_module()

        assert results['changed'] is False
        assert not hasattr(results, 'shell')

    def test_update_user_shell_to_bash(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            shell='bash',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        access = [{'name': 'all', 'role': 'admin'}]
        current = Parameters(
            params=dict(
                user='admin',
                shell='tmsh',
                partition_access=access
            )
        )

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.exists = Mock(return_value=True)
        upm.update_on_device = Mock(return_value=True)
        upm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['shell'] == 'bash'

    def test_update_user_shell_to_bash_mutliple_roles(self, *args):
        set_module_args(dict(
            username_credential='someuser',
            shell='bash',
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

        # Configure the parameters that would be returned by querying the
        # remote device
        access = [
            {'name': 'Common', 'role': 'operator'},
            {'name': 'all', 'role': 'guest'}
        ]
        current = Parameters(
            params=dict(
                user='admin',
                shell='tmsh',
                partition_access=access
            )
        )

        # Override methods to force specific logic in the module to happen
        upm = UnpartitionedManager(module=module, params=module.params)
        upm.exists = Mock(return_value=True)
        upm.update_on_device = Mock(return_value=True)
        upm.read_current_from_device = Mock(return_value=current)

        mm = ModuleManager(module=module)
        mm.is_version_less_than_13 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=upm)

        msg = "Shell access is only available to 'admin' or " \
              "'resource-admin' roles."

        with pytest.raises(F5ModuleError) as ex:
            mm.exec_module()
        assert str(ex.value) == msg

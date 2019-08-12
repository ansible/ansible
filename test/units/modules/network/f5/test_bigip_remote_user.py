# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
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
    from library.modules.bigip_remote_user import ApiParameters
    from library.modules.bigip_remote_user import ModuleParameters
    from library.modules.bigip_remote_user import ModuleManager
    from library.modules.bigip_remote_user import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_remote_user import ApiParameters
    from ansible.modules.network.f5.bigip_remote_user import ModuleParameters
    from ansible.modules.network.f5.bigip_remote_user import ModuleManager
    from ansible.modules.network.f5.bigip_remote_user import ArgumentSpec

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock

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
            default_partition='Common',
            default_role='admin',
            console_access='yes',
            description='this is a role'

        )

        p = ModuleParameters(params=args)
        assert p.default_partition == 'Common'
        assert p.default_role == 'admin'
        assert p.console_access == 'tmsh'
        assert p.description == 'this is a role'

    def test_api_parameters(self):
        args = load_fixture('load_remote_user_settings.json')
        p = ApiParameters(params=args)
        assert p.default_partition == 'all'
        assert p.default_role == 'no-access'
        assert p.console_access == 'disabled'
        assert p.description is None


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_remote_syslog(self, *args):
        set_module_args(dict(
            default_partition='Foobar',
            default_role='auditor',
            console_access='yes',
            description='this is a role',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_remote_user_settings.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'this is a role'
        assert results['default_partition'] == 'Foobar'
        assert results['default_role'] == 'auditor'
        assert results['console_access'] == 'yes'

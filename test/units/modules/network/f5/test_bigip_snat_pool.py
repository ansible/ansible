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
    from library.modules.bigip_snat_pool import ModuleParameters
    from library.modules.bigip_snat_pool import ApiParameters
    from library.modules.bigip_snat_pool import ModuleManager
    from library.modules.bigip_snat_pool import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_snat_pool import ModuleParameters
    from ansible.modules.network.f5.bigip_snat_pool import ApiParameters
    from ansible.modules.network.f5.bigip_snat_pool import ModuleManager
    from ansible.modules.network.f5.bigip_snat_pool import ArgumentSpec

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
            name='my-snat-pool',
            state='present',
            members=['10.10.10.10', '20.20.20.20'],
            description='A SNAT pool description',
            partition='Common'
        )
        p = ModuleParameters(params=args)
        assert p.name == 'my-snat-pool'
        assert p.state == 'present'
        assert p.description == 'A SNAT pool description'
        assert len(p.members) == 2
        assert '/Common/10.10.10.10' in p.members
        assert '/Common/20.20.20.20' in p.members

    def test_api_parameters(self):
        args = dict(
            members=['/Common/10.10.10.10', '/foo/20.20.20.20']
        )
        p = ApiParameters(params=args)
        assert len(p.members) == 2
        assert '/Common/10.10.10.10' in p.members
        assert '/foo/20.20.20.20' in p.members


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_snat_pool(self, *args):
        set_module_args(dict(
            name='my-snat-pool',
            state='present',
            members=['10.10.10.10', '20.20.20.20'],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert len(results['members']) == 2
        assert '/Common/10.10.10.10' in results['members']
        assert '/Common/20.20.20.20' in results['members']

    def test_create_snat_pool_idempotent(self, *args):
        set_module_args(dict(
            name='asdasd',
            state='present',
            members=['1.1.1.1', '2.2.2.2'],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_ltm_snatpool.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, True])
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_update_snat_pool(self, *args):
        set_module_args(dict(
            name='asdasd',
            state='present',
            members=['30.30.30.30'],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_ltm_snatpool.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=True)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert len(results['members']) == 1
        assert '/Common/30.30.30.30' in results['members']

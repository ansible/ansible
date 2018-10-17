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
    from library.modules.bigip_snat_pool import Parameters
    from library.modules.bigip_snat_pool import ModuleManager
    from library.modules.bigip_snat_pool import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_snat_pool import Parameters
        from ansible.modules.network.f5.bigip_snat_pool import ModuleManager
        from ansible.modules.network.f5.bigip_snat_pool import ArgumentSpec
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
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


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            name='my-snat-pool',
            state='present',
            members=['10.10.10.10', '20.20.20.20'],
            partition='Common'
        )
        p = Parameters(params=args)
        assert p.name == 'my-snat-pool'
        assert p.state == 'present'
        assert len(p.members) == 2
        assert '/Common/10.10.10.10' in p.members
        assert '/Common/20.20.20.20' in p.members

    def test_api_parameters(self):
        args = dict(
            members=['/Common/10.10.10.10', '/foo/20.20.20.20']
        )
        p = Parameters(params=args)
        assert len(p.members) == 2
        assert '/Common/10.10.10.10' in p.members
        assert '/Common/20.20.20.20' in p.members


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_snat_pool(self, *args):
        set_module_args(dict(
            name='my-snat-pool',
            state='present',
            members=['10.10.10.10', '20.20.20.20'],
            password='passsword',
            server='localhost',
            user='admin'
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
        assert len(results['members']) == 2
        assert '/Common/10.10.10.10' in results['members']
        assert '/Common/20.20.20.20' in results['members']

    def test_create_snat_pool_idempotent(self, *args):
        set_module_args(dict(
            name='asdasd',
            state='present',
            members=['1.1.1.1', '2.2.2.2'],
            password='passsword',
            server='localhost',
            user='admin'
        ))

        current = Parameters(params=load_fixture('load_ltm_snatpool.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
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
            password='passsword',
            server='localhost',
            user='admin'
        ))

        current = Parameters(params=load_fixture('load_ltm_snatpool.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
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

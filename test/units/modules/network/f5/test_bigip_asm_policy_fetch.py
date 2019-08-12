# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
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
    from library.modules.bigip_asm_policy_fetch import ModuleParameters
    from library.modules.bigip_asm_policy_fetch import ModuleManager
    from library.modules.bigip_asm_policy_fetch import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_asm_policy_fetch import ModuleParameters
    from ansible.modules.network.f5.bigip_asm_policy_fetch import ModuleManager
    from ansible.modules.network.f5.bigip_asm_policy_fetch import ArgumentSpec

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
            inline='yes',
            compact='no',
            base64='yes',
            dest='/tmp/foo.xml',
            force='yes',
            file='foo.xml'
        )
        p = ModuleParameters(params=args)
        assert p.inline is True
        assert p.compact is False
        assert p.base64 is True
        assert p.file == 'foo.xml'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

        try:
            self.p1 = patch('library.modules.bigip_asm_policy_fetch.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_asm_policy_fetch.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True

    def tearDown(self):
        self.patcher1.stop()
        self.p1.stop()

    def test_create(self, *args):
        set_module_args(dict(
            name='fake_policy',
            file='foobar.xml',
            dest='/tmp/foobar.xml',
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

        mp = ModuleParameters(params=module.params)
        mp._policy_exists = Mock(return_value=True)
        mm = ModuleManager(module=module)
        mm.want = Mock(return_value=mp)
        mm.want.binary = False
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        mm.execute = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

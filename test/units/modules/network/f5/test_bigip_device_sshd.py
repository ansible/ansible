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
    from library.modules.bigip_device_sshd import ApiParameters
    from library.modules.bigip_device_sshd import ModuleParameters
    from library.modules.bigip_device_sshd import ModuleManager
    from library.modules.bigip_device_sshd import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_device_sshd import ApiParameters
    from ansible.modules.network.f5.bigip_device_sshd import ModuleParameters
    from ansible.modules.network.f5.bigip_device_sshd import ModuleManager
    from ansible.modules.network.f5.bigip_device_sshd import ArgumentSpec

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
            allow=['all'],
            banner='enabled',
            banner_text='asdf',
            inactivity_timeout='100',
            log_level='debug',
            login='enabled',
            port=1010,
        )
        p = ModuleParameters(params=args)
        assert p.allow == ['all']
        assert p.banner == 'enabled'
        assert p.banner_text == 'asdf'
        assert p.inactivity_timeout == 100
        assert p.log_level == 'debug'
        assert p.login == 'enabled'
        assert p.port == 1010


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update_settings(self, *args):
        set_module_args(dict(
            allow=['all'],
            banner='enabled',
            banner_text='asdf',
            inactivity_timeout='100',
            log_level='debug',
            login='enabled',
            port=1010,
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(
            params=dict(
                allow=['172.27.1.1']
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['allow'] == ['all']

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
    from library.modules.bigip_device_dns import Parameters
    from library.modules.bigip_device_dns import ModuleManager
    from library.modules.bigip_device_dns import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_device_dns import Parameters
    from ansible.modules.network.f5.bigip_device_dns import ModuleManager
    from ansible.modules.network.f5.bigip_device_dns import ArgumentSpec

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
            cache='disable',
            ip_version=4,
            name_servers=['10.10.10.10', '11.11.11.11'],
            search=['14.14.14.14', '15.15.15.15'],
        )
        p = Parameters(params=args)
        assert p.cache == 'disable'
        assert p.name_servers == ['10.10.10.10', '11.11.11.11']
        assert p.search == ['14.14.14.14', '15.15.15.15']

        # BIG-IP considers "ipv4" to be an empty value
        assert p.ip_version == 4

    def test_ipv6_parameter(self):
        args = dict(
            ip_version=6
        )
        p = Parameters(params=args)
        assert p.ip_version == 6


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update_settings(self, *args):
        set_module_args(dict(
            cache='disable',
            ip_version=4,
            name_servers=['10.10.10.10', '11.11.11.11'],
            search=['14.14.14.14', '15.15.15.15'],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(
            dict(
                cache='enable'
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True

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
    from library.modules.bigip_dns_zone import ApiParameters
    from library.modules.bigip_dns_zone import ModuleParameters
    from library.modules.bigip_dns_zone import ModuleManager
    from library.modules.bigip_dns_zone import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_dns_zone import ApiParameters
    from ansible.modules.network.f5.bigip_dns_zone import ModuleParameters
    from ansible.modules.network.f5.bigip_dns_zone import ModuleManager
    from ansible.modules.network.f5.bigip_dns_zone import ArgumentSpec

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
            name='foo',
            dns_express=dict(
                server='server1',
                enabled=True,
                notify_action='consume',
                allow_notify_from=['1.1.1.1'],
                verify_tsig=True,
                response_policy=False
            ),
            nameservers=[
                'foo', 'bar', 'baz'
            ],
            tsig_server_key='key1'
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert len(p.nameservers) == 3
        assert p.tsig_server_key == '/Common/key1'
        assert p.express_server == '/Common/server1'
        assert p.enabled == 'yes'
        assert p.notify_action == 'consume'
        assert len(p.allow_notify_from) == 1
        assert p.verify_tsig == 'yes'
        assert p.response_policy == 'no'

    def test_api_parameters(self):
        args = load_fixture('load_ltm_dns_zone_1.json')
        p = ApiParameters(params=args)
        assert p.name == 'foo'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            name='foo',
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
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

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
    from library.modules.bigip_device_auth_ldap import ApiParameters
    from library.modules.bigip_device_auth_ldap import ModuleParameters
    from library.modules.bigip_device_auth_ldap import ModuleManager
    from library.modules.bigip_device_auth_ldap import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_device_auth_ldap import ApiParameters
    from ansible.modules.network.f5.bigip_device_auth_ldap import ModuleParameters
    from ansible.modules.network.f5.bigip_device_auth_ldap import ModuleManager
    from ansible.modules.network.f5.bigip_device_auth_ldap import ArgumentSpec

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
            servers=['10.10.10.10', '10.10.10.11'],
            port=389,
            remote_directory_tree='foo',
            scope='base',
            bind_dn='bar',
            bind_password='secret',
            user_template='alice',
            check_member_attr=False,
            ssl='no',
            ssl_ca_cert='default.crt',
            ssl_client_key='default.key',
            ssl_client_cert='default1.crt',
            ssl_check_peer=True,
            login_ldap_attr='bob',
            fallback_to_local=True,
            update_password='on_create',
        )
        p = ApiParameters(params=args)
        assert p.port == 389
        assert p.servers == ['10.10.10.10', '10.10.10.11']
        assert p.remote_directory_tree == 'foo'
        assert p.scope == 'base'
        assert p.bind_dn == 'bar'
        assert p.bind_password == 'secret'
        assert p.user_template == 'alice'
        assert p.check_member_attr == 'no'
        assert p.ssl == 'no'
        assert p.ssl_ca_cert == '/Common/default.crt'
        assert p.ssl_client_key == '/Common/default.key'
        assert p.ssl_client_cert == '/Common/default1.crt'
        assert p.ssl_check_peer == 'yes'
        assert p.login_ldap_attr == 'bob'
        assert p.fallback_to_local == 'yes'
        assert p.update_password == 'on_create'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            servers=['10.10.10.10', '10.10.10.11'],
            update_password='on_create',
            state='present',
            provider=dict(
                password='admin',
                server='localhost',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        mm.update_auth_source_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True

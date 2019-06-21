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
    from library.modules.bigip_device_httpd import Parameters
    from library.modules.bigip_device_httpd import ModuleManager
    from library.modules.bigip_device_httpd import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_device_httpd import Parameters
    from ansible.modules.network.f5.bigip_device_httpd import ModuleManager
    from ansible.modules.network.f5.bigip_device_httpd import ArgumentSpec

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
            auth_name='BIG-IP',
            auth_pam_idle_timeout=1200,
            auth_pam_validate_ip='on'
        )

        p = Parameters(params=args)
        assert p.auth_name == 'BIG-IP'
        assert p.auth_pam_idle_timeout == 1200
        assert p.auth_pam_validate_ip == 'on'

    def test_api_parameters(self):
        args = load_fixture('load_sys_httpd.json')
        p = Parameters(params=args)
        assert p.auth_name == 'BIG-IP'
        assert p.auth_pam_idle_timeout == 1200


class TestModuleManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_update(self, *args):
        set_module_args(
            dict(
                auth_name='foo',
                auth_pam_idle_timeout='1000',
                auth_pam_validate_ip='off',
                auth_pam_dashboard_timeout='on',
                fast_cgi_timeout=200,
                hostname_lookup='on',
                log_level='error',
                max_clients='20',
                redirect_http_to_https='yes',
                ssl_port=8443,
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        current = Parameters(params=load_fixture('load_sys_httpd.json'))

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

    def test_update_issue_00522(self, *args):
        set_module_args(
            dict(
                ssl_cipher_suite='ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384',
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        current = Parameters(params=load_fixture('load_sys_httpd.json'))

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
        assert results['ssl_cipher_suite'] == 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384'

    def test_update_issue_00522_as_list(self, *args):
        set_module_args(
            dict(
                ssl_cipher_suite=[
                    'ECDHE-RSA-AES128-GCM-SHA256',
                    'ECDHE-RSA-AES256-GCM-SHA384'
                ],
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        current = Parameters(params=load_fixture('load_sys_httpd.json'))

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
        assert results['ssl_cipher_suite'] == 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384'

    def test_update_issue_00522_default(self, *args):
        set_module_args(
            dict(
                ssl_cipher_suite='default',
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        current = Parameters(params=load_fixture('load_sys_httpd_non_default.json'))

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
        assert results['ssl_cipher_suite'] == 'default'

    def test_update_issue_00587(self, *args):
        set_module_args(
            dict(
                ssl_protocols='all -SSLv2',
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        current = Parameters(params=load_fixture('load_sys_httpd.json'))

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
        assert results['ssl_protocols'] == 'all -SSLv2'

    def test_update_issue_00587_as_list(self, *args):
        set_module_args(
            dict(
                ssl_protocols=[
                    'all',
                    '-SSLv2'
                ],
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        current = Parameters(params=load_fixture('load_sys_httpd.json'))

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
        assert results['ssl_protocols'] == 'all -SSLv2'

    def test_update_issue_00587_default(self, *args):
        set_module_args(
            dict(
                ssl_protocols='default',
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            )
        )

        current = Parameters(params=load_fixture('load_sys_httpd_non_default.json'))

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
        assert results['ssl_protocols'] == 'default'

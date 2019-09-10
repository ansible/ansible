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
    from library.modules.bigip_device_certificate import ModuleParameters
    from library.modules.bigip_device_certificate import ModuleManager
    from library.modules.bigip_device_certificate import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_device_certificate import ModuleParameters
    from ansible.modules.network.f5.bigip_device_certificate import ModuleManager
    from ansible.modules.network.f5.bigip_device_certificate import ArgumentSpec

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
            key_size=2048,
            cert_name='foo.crt',
            key_name='foo.key',
            days_valid=60,
            issuer=dict(
                country='US',
                state='WA',
                locality='Seattle',
                organization='F5',
                division='IT',
                common_name='foo.bar.local',
                email='admin@foo.bar.local'
            ),
            new_cert='yes'
        )
        p = ModuleParameters(params=args)
        assert p.key_size == 2048
        assert p.cert_name == 'foo.crt'
        assert p.key_name == 'foo.key'
        assert p.days_valid == 60
        assert 'CN=foo.bar.local' in p.issuer


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update_expired_cert(self, *args):
        set_module_args(dict(
            days_valid=60,
            provider=dict(
                server='localhost',
                password='password',
                user='admin',
                transport='cli',
                server_port=22
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )

        mm = ModuleManager(module=module)
        mm.expired = Mock(return_value=True)
        mm.update_certificate = Mock(return_value=True)
        mm.restart_daemon = Mock(return_value=True)
        mm.copy_files_to_trusted = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['days_valid'] == 60

    def test_create_new_cert(self):
        set_module_args(dict(
            key_size=2048,
            cert_name='foo.crt',
            key_name='foo.key',
            days_valid=60,
            new_cert='yes',
            issuer=dict(
                country='US',
                state='WA',
                locality='Seattle',
                organization='F5',
                division='IT',
                common_name='foo.bar.local',
                email='admin@foo.bar.local'
            ),
            provider=dict(
                server='localhost',
                password='password',
                user='admin',
                transport='cli',
                server_port=22
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )

        mm = ModuleManager(module=module)
        mm.expired = Mock(return_value=True)
        mm.generate_cert_key = Mock(return_value=True)
        mm.restart_daemon = Mock(return_value=True)
        mm.configure_new_cert = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['days_valid'] == 60
        assert results['cert_name'] == 'foo.crt'
        assert results['key_name'] == 'foo.key'
        assert results['issuer'] == dict(
            country='US',
            state='WA',
            locality='Seattle',
            organization='F5',
            division='IT',
            common_name='foo.bar.local',
            email='admin@foo.bar.local'
        )

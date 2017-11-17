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
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils.f5_utils import AnsibleF5Client
from units.modules.utils import set_module_args

try:
    from library.bigip_ssl_certificate import ArgumentSpec
    from library.bigip_ssl_certificate import KeyParameters
    from library.bigip_ssl_certificate import CertParameters
    from library.bigip_ssl_certificate import CertificateManager
    from library.bigip_ssl_certificate import HAS_F5SDK
    from library.bigip_ssl_certificate import KeyManager
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_ssl_certificate import ArgumentSpec
        from ansible.modules.network.f5.bigip_ssl_certificate import KeyParameters
        from ansible.modules.network.f5.bigip_ssl_certificate import CertParameters
        from ansible.modules.network.f5.bigip_ssl_certificate import CertificateManager
        from ansible.modules.network.f5.bigip_ssl_certificate import HAS_F5SDK
        from ansible.modules.network.f5.bigip_ssl_certificate import KeyManager
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
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
    def test_module_parameters_key(self):
        key_content = load_fixture('create_insecure_key1.key')
        args = dict(
            key_content=key_content,
            name="cert1",
            partition="Common",
            state="present",
            password='password',
            server='localhost',
            user='admin'
        )
        p = KeyParameters(args)
        assert p.name == 'cert1'
        assert p.key_filename == 'cert1.key'
        assert '-----BEGIN RSA PRIVATE KEY-----' in p.key_content
        assert '-----END RSA PRIVATE KEY-----' in p.key_content
        assert p.key_checksum == '91bdddcf0077e2bb2a0258aae2ae3117be392e83'
        assert p.state == 'present'
        assert p.user == 'admin'
        assert p.server == 'localhost'
        assert p.password == 'password'
        assert p.partition == 'Common'

    def test_module_parameters_cert(self):
        cert_content = load_fixture('create_insecure_cert1.crt')
        args = dict(
            cert_content=cert_content,
            name="cert1",
            partition="Common",
            state="present",
            password='password',
            server='localhost',
            user='admin'
        )
        p = CertParameters(args)
        assert p.name == 'cert1'
        assert p.cert_filename == 'cert1.crt'
        assert 'Signature Algorithm' in p.cert_content
        assert '-----BEGIN CERTIFICATE-----' in p.cert_content
        assert '-----END CERTIFICATE-----' in p.cert_content
        assert p.cert_checksum == '1e55aa57ee166a380e756b5aa4a835c5849490fe'
        assert p.state == 'present'
        assert p.user == 'admin'
        assert p.server == 'localhost'
        assert p.password == 'password'
        assert p.partition == 'Common'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestCertificateManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_import_certificate_and_key_no_key_passphrase(self, *args):
        set_module_args(dict(
            name='foo',
            cert_content=load_fixture('cert1.crt'),
            key_content=load_fixture('cert1.key'),
            state='present',
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        cm = CertificateManager(client)
        cm.exists = Mock(side_effect=[False, True])
        cm.create_on_device = Mock(return_value=True)

        results = cm.exec_module()

        assert results['changed'] is True

    def test_import_certificate_chain(self, *args):
        set_module_args(dict(
            name='foo',
            cert_content=load_fixture('chain1.crt'),
            state='present',
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        cm = CertificateManager(client)
        cm.exists = Mock(side_effect=[False, True])
        cm.create_on_device = Mock(return_value=True)

        results = cm.exec_module()

        assert results['changed'] is True


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestKeyManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_import_certificate_and_key_no_key_passphrase(self, *args):
        set_module_args(dict(
            name='foo',
            cert_content=load_fixture('cert1.crt'),
            key_content=load_fixture('cert1.key'),
            state='present',
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        cm = KeyManager(client)
        cm.exists = Mock(side_effect=[False, True])
        cm.create_on_device = Mock(return_value=True)

        results = cm.exec_module()

        assert results['changed'] is True

    def test_update_certificate_new_certificate_and_key_password_protected_key(self, *args):
        set_module_args(dict(
            name='foo',
            cert_content=load_fixture('cert2.crt'),
            key_content=load_fixture('cert2.key'),
            state='present',
            passphrase='keypass',
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        cm = KeyManager(client)
        cm.exists = Mock(side_effect=[False, True])
        cm.create_on_device = Mock(return_value=True)

        results = cm.exec_module()

        assert results['changed'] is True

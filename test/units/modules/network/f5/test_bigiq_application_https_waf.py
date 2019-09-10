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
    from library.modules.bigiq_application_https_waf import ModuleParameters
    from library.modules.bigiq_application_https_waf import ModuleManager
    from library.modules.bigiq_application_https_waf import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigiq_application_https_waf import ModuleParameters
    from ansible.modules.network.f5.bigiq_application_https_waf import ModuleManager
    from ansible.modules.network.f5.bigiq_application_https_waf import ArgumentSpec
    from ansible.module_utils.network.f5.common import F5ModuleError

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
            name='foo',
            description='my description',
            service_environment='bar',
            servers=[
                dict(
                    address='1.2.3.4',
                    port=8080
                ),
                dict(
                    address='5.6.7.8',
                    port=8000
                )
            ],
            inbound_virtual=dict(
                address='2.2.2.2',
                netmask='255.255.255.255',
                port=80
            ),
            redirect_virtual=dict(
                address='3.3.3.3',
                netmask='255.255.255.255',
                port=80
            ),
            domain_names=[
                'foo.baz.com',
                'bar.baz.com'
            ]
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.config_set_name == 'foo'
        assert p.sub_path == 'foo'
        assert p.http_profile == 'profile_http'
        assert p.service_environment == 'bar'
        assert len(p.servers) == 2
        assert 'address' in p.servers[0]
        assert 'port' in p.servers[0]
        assert 'address' in p.servers[1]
        assert 'port' in p.servers[1]
        assert p.servers[0]['address'] == '1.2.3.4'
        assert p.servers[0]['port'] == 8080
        assert p.servers[1]['address'] == '5.6.7.8'
        assert p.servers[1]['port'] == 8000
        assert 'address' in p.inbound_virtual
        assert 'netmask' in p.inbound_virtual
        assert 'port' in p.inbound_virtual
        assert p.inbound_virtual['address'] == '2.2.2.2'
        assert p.inbound_virtual['netmask'] == '255.255.255.255'
        assert p.inbound_virtual['port'] == 80
        assert 'address' in p.redirect_virtual
        assert 'netmask' in p.redirect_virtual
        assert 'port' in p.redirect_virtual
        assert p.redirect_virtual['address'] == '3.3.3.3'
        assert p.redirect_virtual['netmask'] == '255.255.255.255'
        assert p.redirect_virtual['port'] == 80


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

        try:
            self.p1 = patch('library.modules.bigiq_application_https_waf.bigiq_version')
            self.p2 = patch('library.modules.bigiq_application_https_waf.ModuleParameters.template_reference')
            self.p3 = patch('library.modules.bigiq_application_https_waf.ModuleParameters.ssg_reference')
            self.p4 = patch('library.modules.bigiq_application_https_waf.ModuleParameters.default_device_reference')

            self.m1 = self.p1.start()
            self.m2 = self.p2.start()
            self.m3 = self.p3.start()
            self.m4 = self.p4.start()

            self.m1.return_value = '6.1.0'
            self.m2.return_value = Mock(return_value='https://localhost/mgmt/foobar1')
            self.m3.return_value = Mock(return_value='https://localhost/mgmt/foobar2')
            self.m4.return_value = Mock(return_value='https://localhost/mgmt/foobar3')

        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigiq_application_https_waf.bigiq_version')
            self.p2 = patch('ansible.modules.network.f5.bigiq_application_https_waf.ModuleParameters.template_reference')
            self.p3 = patch('ansible.modules.network.f5.bigiq_application_https_waf.ModuleParameters.ssg_reference')
            self.p4 = patch('ansible.modules.network.f5.bigiq_application_https_waf.ModuleParameters.default_device_reference')

            self.m1 = self.p1.start()
            self.m2 = self.p2.start()
            self.m3 = self.p3.start()
            self.m4 = self.p4.start()

            self.m1.return_value = '6.1.0'
            self.m2.return_value = Mock(return_value='https://localhost/mgmt/foobar1')
            self.m3.return_value = Mock(return_value='https://localhost/mgmt/foobar2')
            self.m4.return_value = Mock(return_value='https://localhost/mgmt/foobar3')

    def tearDown(self):
        self.patcher1.stop()
        self.p1.stop()
        self.p2.stop()
        self.p3.stop()
        self.p4.stop()

    def test_create(self, *args):
        set_module_args(dict(
            name='foo',
            description='my description',
            service_environment='bar',
            servers=[
                dict(
                    address='1.2.3.4',
                    port=8080
                ),
                dict(
                    address='5.6.7.8',
                    port=8000
                )
            ],
            inbound_virtual=dict(
                address='2.2.2.2',
                netmask='255.255.255.255',
                port=80
            ),
            redirect_virtual=dict(
                address='3.3.3.3',
                netmask='255.255.255.255',
                port=80
            ),
            domain_names=[
                'foo.baz.com',
                'bar.baz.com'
            ],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.check_bigiq_version = Mock(return_value=True)
        mm.has_no_service_environment = Mock(return_value=False)
        mm.wait_for_apply_template_task = Mock(return_value=True)

        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(side_effect=[False, True])

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'my description'

    def test_bigiq_version_raises(self):
        set_module_args(dict(
            name='foo',
            description='my description',
            service_environment='bar',
            servers=[
                dict(
                    address='1.2.3.4',
                    port=8080
                ),
                dict(
                    address='5.6.7.8',
                    port=8000
                )
            ],
            inbound_virtual=dict(
                address='2.2.2.2',
                netmask='255.255.255.255',
                port=80
            ),
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive
        )

        msg = 'Module supports only BIGIQ version 6.0.x or lower.'
        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)

        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()
        assert str(err.value) == msg

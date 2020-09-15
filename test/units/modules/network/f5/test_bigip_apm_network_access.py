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
    from library.modules.bigip_apm_network_access import ApiParameters
    from library.modules.bigip_apm_network_access import ModuleParameters
    from library.modules.bigip_apm_network_access import ModuleManager
    from library.modules.bigip_apm_network_access import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_apm_network_access import ApiParameters
    from ansible.modules.network.f5.bigip_apm_network_access import ModuleParameters
    from ansible.modules.network.f5.bigip_apm_network_access import ModuleManager
    from ansible.modules.network.f5.bigip_apm_network_access import ArgumentSpec

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
            ip_version='ipv4',
            split_tunnel=True,
            description='foobar',
            allow_local_subnet=True,
            allow_local_dns=True,
            snat_pool='foo_pool',
            dtls=True,
            dtls_port=4443,
            ipv4_lease_pool='ipv4lease',
            excluded_ipv4_adresses=[dict(subnet='10.10.10.1')],
            ipv4_address_space=[dict(subnet='192.168.1.0/24')],
            dns_address_space=['foobar.com'],
            excluded_dns_addresses=['bar-foo.org']
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.ip_version == 'ipv4'
        assert p.split_tunnel == 'true'
        assert p.allow_local_subnet == 'true'
        assert p.allow_local_dns == 'true'
        assert p.snat_pool == '/Common/foo_pool'
        assert p.description == 'foobar'
        assert p.dtls == 'true'
        assert p.dtls_port == 4443
        assert p.ipv4_lease_pool == '/Common/ipv4lease'
        assert p.excluded_ipv4_adresses == [dict(subnet='10.10.10.1/32')]
        assert p.ipv4_address_space == [dict(subnet='192.168.1.0/24')]
        assert p.dns_address_space == ['foobar.com']
        assert p.excluded_dns_addresses == ['bar-foo.org']

    def test_api_parameters(self):
        args = load_fixture('load_apm_network_access.json')

        p = ApiParameters(params=args)
        assert p.name == 'test'
        assert p.ip_version == 'ipv4-ipv6'
        assert p.split_tunnel == 'true'
        assert p.allow_local_subnet == 'true'
        assert p.allow_local_dns == 'true'
        assert p.snat_pool == 'automap'
        assert p.dtls == 'false'
        assert p.dtls_port == 4433
        assert p.ipv4_lease_pool == '/Common/ipv4lease'
        assert p.excluded_ipv4_adresses == [
            dict(subnet='192.168.1.0/24'),
            dict(subnet='192.168.2.1/32')
        ]
        assert p.ipv4_address_space == [
            dict(subnet='10.10.10.1/32'),
            dict(subnet='10.11.11.0/24')
        ]
        assert p.dns_address_space == ['foo.com', 'bar.com']
        assert p.excluded_dns_addresses == ['baz.com', 'bazfoo.com']
        assert p.ipv6_address_space == [dict(subnet="2607:f0d0:1002:51::4/128")]


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_ipv4_net_access(self, *args):
        set_module_args(dict(
            name='foo',
            ip_version='ipv4',
            split_tunnel=True,
            description='foobar',
            allow_local_subnet=True,
            allow_local_dns=True,
            snat_pool='foo_pool',
            dtls=True,
            dtls_port=4443,
            ipv4_lease_pool='ipv4lease',
            excluded_ipv4_adresses=[dict(subnet='10.10.10.1')],
            ipv4_address_space=[dict(subnet='192.168.1.0/24')],
            dns_address_space=['foobar.com'],
            excluded_dns_addresses=['bar-foo.org'],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['ip_version'] == 'ipv4'
        assert results['split_tunnel'] == 'yes'
        assert results['allow_local_subnet'] == 'yes'
        assert results['allow_local_dns'] == 'yes'
        assert results['snat_pool'] == '/Common/foo_pool'
        assert results['description'] == 'foobar'
        assert results['dtls'] == 'yes'
        assert results['dtls_port'] == 4443
        assert results['ipv4_lease_pool'] == '/Common/ipv4lease'
        assert results['excluded_ipv4_adresses'] == [dict(subnet='10.10.10.1')]
        assert results['ipv4_address_space'] == [dict(subnet='192.168.1.0/24')]
        assert results['dns_address_space'] == ['foobar.com']
        assert results['excluded_dns_addresses'] == ['bar-foo.org']

    def test_update_ipv4_net_access(self, *args):
        set_module_args(dict(
            name='test',
            excluded_ipv4_adresses=[dict(subnet='10.10.10.1')],
            ipv4_address_space=[dict(subnet='192.168.1.0/24')],
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_apm_network_access.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['excluded_ipv4_adresses'] == [dict(subnet='10.10.10.1')]
        assert results['ipv4_address_space'] == [dict(subnet='192.168.1.0/24')]

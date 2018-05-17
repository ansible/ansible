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

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_snmp_community import ApiParameters
    from library.modules.bigip_snmp_community import ModuleParameters
    from library.modules.bigip_snmp_community import ModuleManager
    from library.modules.bigip_snmp_community import V1Manager
    from library.modules.bigip_snmp_community import V2Manager
    from library.modules.bigip_snmp_community import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_snmp_community import ApiParameters
        from ansible.modules.network.f5.bigip_snmp_community import ModuleParameters
        from ansible.modules.network.f5.bigip_snmp_community import ModuleManager
        from ansible.modules.network.f5.bigip_snmp_community import V1Manager
        from ansible.modules.network.f5.bigip_snmp_community import V2Manager
        from ansible.modules.network.f5.bigip_snmp_community import ArgumentSpec
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
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
    def test_module_parameters(self):
        args = dict(
            version='v2c',
            community='foo',
            source='1.1.1.1',
            port='8080',
            oid='.1',
            access='ro',
            ip_version=4,
            snmp_username='admin',
            snmp_auth_protocol='sha',
            snmp_auth_password='secretsecret',
            snmp_privacy_protocol='des',
            snmp_privacy_password='secretsecret',
            update_password='always',
            state='present'
        )

        p = ModuleParameters(params=args)
        assert p.version == 'v2c'
        assert p.community == 'foo'
        assert p.source == '1.1.1.1'
        assert p.port == 8080
        assert p.oid == '.1'
        assert p.access == 'ro'
        assert p.ip_version == 4
        assert p.snmp_username == 'admin'
        assert p.snmp_auth_protocol == 'sha'
        assert p.snmp_auth_password == 'secretsecret'
        assert p.snmp_privacy_protocol == 'des'
        assert p.snmp_privacy_password == 'secretsecret'
        assert p.update_password == 'always'
        assert p.state == 'present'

    def test_api_parameters_community_1(self):
        args = load_fixture('load_sys_snmp_communities_1.json')

        p = ApiParameters(params=args)
        assert p.access == 'ro'
        assert p.community == 'foo'
        assert p.ip_version == 4

    def test_api_parameters_community_2(self):
        args = load_fixture('load_sys_snmp_communities_2.json')

        p = ApiParameters(params=args)
        assert p.access == 'rw'
        assert p.community == 'foo'
        assert p.ip_version == 4
        assert p.oid == '.1'
        assert p.source == '1.1.1.1'

    def test_api_parameters_community_3(self):
        args = load_fixture('load_sys_snmp_communities_3.json')

        p = ApiParameters(params=args)
        assert p.access == 'ro'
        assert p.community == 'foo'
        assert p.ip_version == 6
        assert p.oid == '.1'
        assert p.source == '2001:0db8:85a3:0000:0000:8a2e:0370:7334'

    def test_api_parameters_community_4(self):
        args = load_fixture('load_sys_snmp_communities_4.json')

        p = ApiParameters(params=args)
        assert p.access == 'ro'
        assert p.community == 'foo'
        assert p.ip_version == 6

    def test_api_parameters_users_1(self):
        args = load_fixture('load_sys_snmp_users_1.json')

        p = ApiParameters(params=args)
        assert p.access == 'ro'
        assert p.snmp_auth_protocol == 'sha'
        assert p.oid == '.1'
        assert p.snmp_privacy_protocol == 'aes'
        assert p.snmp_username == 'foo'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_v2c_community_1(self, *args):
        set_module_args(dict(
            version='v2c',
            community='foo',
            source='1.1.1.1',
            port='8080',
            oid='.1',
            access='ro',
            ip_version=4,
            state='present',
            partition='Common',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        m1 = V1Manager(module=module)

        # Override methods to force specific logic in the module to happen
        m1.exists = Mock(side_effect=[False, True])
        m1.create_on_device = Mock(return_value=True)

        m0 = ModuleManager(module=module)
        m0.get_manager = Mock(return_value=m1)

        results = m0.exec_module()

        assert results['changed'] is True

    def test_create_v1_community_1(self, *args):
        set_module_args(dict(
            version='v1',
            community='foo',
            source='1.1.1.1',
            port='8080',
            oid='.1',
            access='ro',
            ip_version=4,
            state='present',
            partition='Common',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        m1 = V1Manager(module=module)

        # Override methods to force specific logic in the module to happen
        m1.exists = Mock(side_effect=[False, True])
        m1.create_on_device = Mock(return_value=True)

        m0 = ModuleManager(module=module)
        m0.get_manager = Mock(return_value=m1)

        results = m0.exec_module()

        assert results['changed'] is True

    def test_create_v3_community_1(self, *args):
        set_module_args(dict(
            version='v3',
            oid='.1',
            access='ro',
            snmp_username='admin',
            snmp_auth_protocol='md5',
            snmp_auth_password='secretsecret',
            snmp_privacy_protocol='des',
            snmp_privacy_password='secretsecret',
            state='present',
            partition='Common',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        m1 = V2Manager(module=module)

        # Override methods to force specific logic in the module to happen
        m1.exists = Mock(side_effect=[False, True])
        m1.create_on_device = Mock(return_value=True)

        m0 = ModuleManager(module=module)
        m0.get_manager = Mock(return_value=m1)

        results = m0.exec_module()

        assert results['changed'] is True

    def test_create_v3_community_2(self, *args):
        set_module_args(dict(
            version='v3',
            access='ro',
            snmp_username='admin',
            snmp_auth_protocol='md5',
            snmp_auth_password='secretsecret',
            snmp_privacy_protocol='des',
            snmp_privacy_password='secretsecret',
            state='present',
            partition='Common',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        m1 = V2Manager(module=module)

        # Override methods to force specific logic in the module to happen
        m1.exists = Mock(side_effect=[False, True])
        m1.create_on_device = Mock(return_value=True)

        m0 = ModuleManager(module=module)
        m0.get_manager = Mock(return_value=m1)

        with pytest.raises(F5ModuleError) as ex:
            m0.exec_module()

        assert 'oid must be specified when creating a new v3 community.' == str(ex.value)

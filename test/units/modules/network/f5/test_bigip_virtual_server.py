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
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_virtual_server import ModuleParameters
    from library.modules.bigip_virtual_server import ApiParameters
    from library.modules.bigip_virtual_server import ModuleManager
    from library.modules.bigip_virtual_server import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_virtual_server import ApiParameters
        from ansible.modules.network.f5.bigip_virtual_server import ModuleParameters
        from ansible.modules.network.f5.bigip_virtual_server import ModuleManager
        from ansible.modules.network.f5.bigip_virtual_server import ArgumentSpec
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
    def test_destination_mutex_1(self):
        args = dict(
            destination='1.1.1.1'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '1.1.1.1'

    def test_destination_mutex_2(self):
        args = dict(
            destination='1.1.1.1%2'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '1.1.1.1'
        assert p.destination_tuple.route_domain == 2

    def test_destination_mutex_3(self):
        args = dict(
            destination='1.1.1.1:80'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '1.1.1.1'
        assert p.destination_tuple.port == 80

    def test_destination_mutex_4(self):
        args = dict(
            destination='1.1.1.1%2:80'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '1.1.1.1'
        assert p.destination_tuple.port == 80
        assert p.destination_tuple.route_domain == 2

    def test_api_destination_mutex_5(self):
        args = dict(
            destination='/Common/1.1.1.1'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '1.1.1.1'

    def test_api_destination_mutex_6(self):
        args = dict(
            destination='/Common/1.1.1.1%2'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '1.1.1.1'
        assert p.destination_tuple.route_domain == 2

    def test_api_destination_mutex_7(self):
        args = dict(
            destination='/Common/1.1.1.1:80'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '1.1.1.1'
        assert p.destination_tuple.port == 80

    def test_api_destination_mutex_8(self):
        args = dict(
            destination='/Common/1.1.1.1%2:80'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '1.1.1.1'
        assert p.destination_tuple.port == 80
        assert p.destination_tuple.route_domain == 2

    def test_destination_mutex_9(self):
        args = dict(
            destination='2700:bc00:1f10:101::6'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '2700:bc00:1f10:101::6'

    def test_destination_mutex_10(self):
        args = dict(
            destination='2700:bc00:1f10:101::6%2'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '2700:bc00:1f10:101::6'
        assert p.destination_tuple.route_domain == 2

    def test_destination_mutex_11(self):
        args = dict(
            destination='2700:bc00:1f10:101::6.80'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '2700:bc00:1f10:101::6'
        assert p.destination_tuple.port == 80

    def test_destination_mutex_12(self):
        args = dict(
            destination='2700:bc00:1f10:101::6%2.80'
        )
        p = ApiParameters(params=args)
        assert p.destination_tuple.ip == '2700:bc00:1f10:101::6'
        assert p.destination_tuple.port == 80
        assert p.destination_tuple.route_domain == 2

    def test_module_no_partition_prefix_parameters(self):
        args = dict(
            server='localhost',
            user='admin',
            password='secret',
            state='present',
            partition='Common',
            name='my-virtual-server',
            destination='10.10.10.10',
            port=443,
            pool='my-pool',
            snat='Automap',
            description='Test Virtual Server',
            profiles=[
                dict(
                    name='fix',
                    context='all'
                )
            ],
            enabled_vlans=['vlan2']
        )
        p = ModuleParameters(params=args)
        assert p.name == 'my-virtual-server'
        assert p.partition == 'Common'
        assert p.port == 443
        assert p.server == 'localhost'
        assert p.user == 'admin'
        assert p.password == 'secret'
        assert p.destination == '/Common/10.10.10.10:443'
        assert p.pool == '/Common/my-pool'
        assert p.snat == {'type': 'automap'}
        assert p.description == 'Test Virtual Server'
        assert len(p.profiles) == 1
        assert 'context' in p.profiles[0]
        assert 'name' in p.profiles[0]
        assert '/Common/vlan2' in p.enabled_vlans

    def test_module_partition_prefix_parameters(self):
        args = dict(
            server='localhost',
            user='admin',
            password='secret',
            state='present',
            partition='Common',
            name='my-virtual-server',
            destination='10.10.10.10',
            port=443,
            pool='/Common/my-pool',
            snat='Automap',
            description='Test Virtual Server',
            profiles=[
                dict(
                    name='fix',
                    context='all'
                )
            ],
            enabled_vlans=['/Common/vlan2']
        )
        p = ModuleParameters(params=args)
        assert p.name == 'my-virtual-server'
        assert p.partition == 'Common'
        assert p.port == 443
        assert p.server == 'localhost'
        assert p.user == 'admin'
        assert p.password == 'secret'
        assert p.destination == '/Common/10.10.10.10:443'
        assert p.pool == '/Common/my-pool'
        assert p.snat == {'type': 'automap'}
        assert p.description == 'Test Virtual Server'
        assert len(p.profiles) == 1
        assert 'context' in p.profiles[0]
        assert 'name' in p.profiles[0]
        assert '/Common/vlan2' in p.enabled_vlans

    def test_api_parameters_variables(self):
        args = {
            "kind": "tm:ltm:virtual:virtualstate",
            "name": "my-virtual-server",
            "partition": "Common",
            "fullPath": "/Common/my-virtual-server",
            "generation": 54,
            "selfLink": "https://localhost/mgmt/tm/ltm/virtual/~Common~my-virtual-server?expandSubcollections=true&ver=12.1.2",
            "addressStatus": "yes",
            "autoLasthop": "default",
            "cmpEnabled": "yes",
            "connectionLimit": 0,
            "description": "Test Virtual Server",
            "destination": "/Common/10.10.10.10:443",
            "enabled": True,
            "gtmScore": 0,
            "ipProtocol": "tcp",
            "mask": "255.255.255.255",
            "mirror": "disabled",
            "mobileAppTunnel": "disabled",
            "nat64": "disabled",
            "rateLimit": "disabled",
            "rateLimitDstMask": 0,
            "rateLimitMode": "object",
            "rateLimitSrcMask": 0,
            "serviceDownImmediateAction": "none",
            "source": "0.0.0.0/0",
            "sourceAddressTranslation": {
                "type": "automap"
            },
            "sourcePort": "preserve",
            "synCookieStatus": "not-activated",
            "translateAddress": "enabled",
            "translatePort": "enabled",
            "vlansEnabled": True,
            "vsIndex": 3,
            "vlans": [
                "/Common/net1"
            ],
            "vlansReference": [
                {
                    "link": "https://localhost/mgmt/tm/net/vlan/~Common~net1?ver=12.1.2"
                }
            ],
            "policiesReference": {
                "link": "https://localhost/mgmt/tm/ltm/virtual/~Common~my-virtual-server/policies?ver=12.1.2",
                "isSubcollection": True
            },
            "profilesReference": {
                "link": "https://localhost/mgmt/tm/ltm/virtual/~Common~my-virtual-server/profiles?ver=12.1.2",
                "isSubcollection": True,
                "items": [
                    {
                        "kind": "tm:ltm:virtual:profiles:profilesstate",
                        "name": "http",
                        "partition": "Common",
                        "fullPath": "/Common/http",
                        "generation": 54,
                        "selfLink": "https://localhost/mgmt/tm/ltm/virtual/~Common~my-virtual-server/profiles/~Common~http?ver=12.1.2",
                        "context": "all",
                        "nameReference": {
                            "link": "https://localhost/mgmt/tm/ltm/profile/http/~Common~http?ver=12.1.2"
                        }
                    },
                    {
                        "kind": "tm:ltm:virtual:profiles:profilesstate",
                        "name": "serverssl",
                        "partition": "Common",
                        "fullPath": "/Common/serverssl",
                        "generation": 54,
                        "selfLink": "https://localhost/mgmt/tm/ltm/virtual/~Common~my-virtual-server/profiles/~Common~serverssl?ver=12.1.2",
                        "context": "serverside",
                        "nameReference": {
                            "link": "https://localhost/mgmt/tm/ltm/profile/server-ssl/~Common~serverssl?ver=12.1.2"
                        }
                    },
                    {
                        "kind": "tm:ltm:virtual:profiles:profilesstate",
                        "name": "tcp",
                        "partition": "Common",
                        "fullPath": "/Common/tcp",
                        "generation": 54,
                        "selfLink": "https://localhost/mgmt/tm/ltm/virtual/~Common~my-virtual-server/profiles/~Common~tcp?ver=12.1.2",
                        "context": "all",
                        "nameReference": {
                            "link": "https://localhost/mgmt/tm/ltm/profile/tcp/~Common~tcp?ver=12.1.2"
                        }
                    }
                ]
            }
        }
        p = ApiParameters(params=args)
        assert p.name == 'my-virtual-server'
        assert p.partition == 'Common'
        assert p.port == 443
        assert p.destination == '/Common/10.10.10.10:443'
        assert p.snat == {'type': 'automap'}
        assert p.description == 'Test Virtual Server'
        assert 'context' in p.profiles[0]
        assert 'name' in p.profiles[0]
        assert 'fullPath' in p.profiles[0]
        assert p.profiles[0]['context'] == 'all'
        assert p.profiles[0]['name'] == 'http'
        assert p.profiles[0]['fullPath'] == '/Common/http'
        assert '/Common/net1' in p.vlans

    def test_module_address_translation_enabled(self):
        args = dict(
            address_translation=True
        )
        p = ModuleParameters(params=args)
        assert p.address_translation == 'enabled'

    def test_module_address_translation_disabled(self):
        args = dict(
            address_translation=False
        )
        p = ModuleParameters(params=args)
        assert p.address_translation == 'disabled'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_virtual_server(self, *args):
        set_module_args(dict(
            all_profiles=[
                dict(
                    name='http'
                ),
                dict(
                    name='clientssl'
                )
            ],
            description="Test Virtual Server",
            destination="10.10.10.10",
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            snat="Automap",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True

    def test_delete_virtual_server(self, *args):
        set_module_args(dict(
            all_profiles=[
                'http', 'clientssl'
            ],
            description="Test Virtual Server",
            destination="10.10.10.10",
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            snat="Automap",
            state="absent",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_enable_vs_that_is_already_enabled(self, *args):
        set_module_args(dict(
            all_profiles=[
                'http', 'clientssl'
            ],
            description="Test Virtual Server",
            destination="10.10.10.10",
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            snat="Automap",
            state="absent",
            user="admin",
            validate_certs="no"
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(
            dict(
                agent_status_traps='disabled'
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        results = mm.exec_module()

        assert results['changed'] is False

    def test_modify_port(self, *args):
        set_module_args(dict(
            name="my-virtual-server",
            partition="Common",
            password="secret",
            port="10443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(params=load_fixture('load_ltm_virtual_1.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True

    def test_modify_port_idempotent(self, *args):
        set_module_args(dict(
            name="my-virtual-server",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(params=load_fixture('load_ltm_virtual_1.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        results = mm.exec_module()

        assert results['changed'] is False

    def test_modify_vlans_idempotent(self, *args):
        set_module_args(dict(
            name="my-virtual-server",
            partition="Common",
            password="secret",
            disabled_vlans=[
                "net1"
            ],
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(params=load_fixture('load_ltm_virtual_2.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_modify_profiles(self, *args):
        set_module_args(dict(
            name="my-virtual-server",
            partition="Common",
            password="secret",
            profiles=[
                'http', 'clientssl'
            ],
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(params=load_fixture('load_ltm_virtual_2.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert len(results['profiles']) == 2
        assert 'name' in results['profiles'][0]
        assert 'context' in results['profiles'][0]
        assert results['profiles'][0]['name'] == 'http'
        assert results['profiles'][0]['context'] == 'all'
        assert 'name' in results['profiles'][1]
        assert 'context' in results['profiles'][1]
        assert results['profiles'][1]['name'] == 'clientssl'
        assert results['profiles'][1]['context'] == 'clientside'

    def test_update_virtual_server(self, *args):
        set_module_args(dict(
            profiles=[
                dict(
                    name='http'
                ),
                dict(
                    name='clientssl'
                )
            ],
            description="foo virtual",
            destination="1.1.1.1",
            name="my-virtual-server",
            partition="Common",
            password="secret",
            port="8443",
            server="localhost",
            snat="snat-pool1",
            state="disabled",
            source='1.2.3.4/32',
            user="admin",
            validate_certs="no",
            irules=[
                'irule1',
                'irule2'
            ],
            policies=[
                'policy1',
                'policy2'
            ],
            enabled_vlans=[
                'vlan1',
                'vlan2'
            ],
            pool='my-pool',
            default_persistence_profile='source_addr',
            fallback_persistence_profile='dest_addr'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(params=load_fixture('load_ltm_virtual_3.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['source'] == '1.2.3.4/32'
        assert results['description'] == 'foo virtual'
        assert results['snat'] == '/Common/snat-pool1'
        assert results['destination'] == '1.1.1.1'
        assert results['port'] == 8443
        assert results['default_persistence_profile'] == '/Common/source_addr'
        assert results['fallback_persistence_profile'] == '/Common/dest_addr'

        # policies
        assert len(results['policies']) == 2
        assert '/Common/policy1' in results['policies']
        assert '/Common/policy2' in results['policies']

        # irules
        assert len(results['irules']) == 2
        assert '/Common/irule1' in results['irules']
        assert '/Common/irule2' in results['irules']

        # vlans
        assert len(results['enabled_vlans']) == 2
        assert '/Common/vlan1' in results['enabled_vlans']
        assert '/Common/vlan2' in results['enabled_vlans']

        # profiles
        assert len(results['profiles']) == 2
        assert 'name' in results['profiles'][0]
        assert 'context' in results['profiles'][0]
        assert results['profiles'][0]['name'] == 'http'
        assert results['profiles'][0]['context'] == 'all'
        assert 'name' in results['profiles'][1]
        assert 'context' in results['profiles'][1]
        assert results['profiles'][1]['name'] == 'clientssl'
        assert results['profiles'][1]['context'] == 'clientside'

    def test_create_virtual_server_with_address_translation_bool_true(self, *args):
        set_module_args(dict(
            destination="10.10.10.10",
            address_translation=True,
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['address_translation'] is True

    def test_create_virtual_server_with_address_translation_string_yes(self, *args):
        set_module_args(dict(
            destination="10.10.10.10",
            address_translation='yes',
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['address_translation'] is True

    def test_create_virtual_server_with_address_translation_bool_false(self, *args):
        set_module_args(dict(
            destination="10.10.10.10",
            address_translation=False,
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['address_translation'] is False

    def test_create_virtual_server_with_address_translation_string_no(self, *args):
        set_module_args(dict(
            destination="10.10.10.10",
            address_translation='no',
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['address_translation'] is False

    def test_create_virtual_server_with_port_translation_bool_true(self, *args):
        set_module_args(dict(
            destination="10.10.10.10",
            port_translation=True,
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['port_translation'] is True

    def test_create_virtual_server_with_port_translation_string_yes(self, *args):
        set_module_args(dict(
            destination="10.10.10.10",
            port_translation='yes',
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['port_translation'] is True

    def test_create_virtual_server_with_port_translation_bool_false(self, *args):
        set_module_args(dict(
            destination="10.10.10.10",
            port_translation=False,
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['port_translation'] is False

    def test_create_virtual_server_with_port_translation_string_no(self, *args):
        set_module_args(dict(
            destination="10.10.10.10",
            port_translation='no',
            name="my-snat-pool",
            partition="Common",
            password="secret",
            port="443",
            server="localhost",
            state="present",
            user="admin",
            validate_certs="no"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['port_translation'] is False

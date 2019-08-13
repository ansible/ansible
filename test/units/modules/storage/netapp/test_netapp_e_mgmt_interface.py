# coding=utf-8
# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.modules.storage.netapp.netapp_e_mgmt_interface import MgmtInterface
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type

import mock
from units.compat.mock import PropertyMock


class MgmtInterfaceTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        'api_username': 'rw',
        'api_password': 'password',
        'api_url': 'http://localhost',
        'ssid': '1',
    }

    TEST_DATA = [
        {
            "controllerRef": "070000000000000000000001",
            "controllerSlot": 1,
            "interfaceName": "wan0",
            "interfaceRef": "2800070000000000000000000001000000000000",
            "channel": 1,
            "alias": "creG1g-AP-a",
            "ipv4Enabled": True,
            "ipv4Address": "10.1.1.10",
            "linkStatus": "up",
            "ipv4SubnetMask": "255.255.255.0",
            "ipv4AddressConfigMethod": "configStatic",
            "ipv4GatewayAddress": "10.1.1.1",
            "ipv6Enabled": False,
            "physicalLocation": {
                "slot": 0,
            },
            "dnsProperties": {
                "acquisitionProperties": {
                    "dnsAcquisitionType": "stat",
                    "dnsServers": [
                        {
                            "addressType": "ipv4",
                            "ipv4Address": "10.1.0.250",
                        },
                        {
                            "addressType": "ipv4",
                            "ipv4Address": "10.10.0.20",
                        }
                    ]
                },
                "dhcpAcquiredDnsServers": []
            },
            "ntpProperties": {
                "acquisitionProperties": {
                    "ntpAcquisitionType": "disabled",
                    "ntpServers": None
                },
                "dhcpAcquiredNtpServers": []
            },
        },
        {
            "controllerRef": "070000000000000000000001",
            "controllerSlot": 1,
            "interfaceName": "wan1",
            "interfaceRef": "2800070000000000000000000001000000000000",
            "channel": 2,
            "alias": "creG1g-AP-a",
            "ipv4Enabled": True,
            "ipv4Address": "0.0.0.0",
            "ipv4SubnetMask": "0.0.0.0",
            "ipv4AddressConfigMethod": "configDhcp",
            "ipv4GatewayAddress": "10.1.1.1",
            "ipv6Enabled": False,
            "physicalLocation": {
                "slot": 1,
            },
            "dnsProperties": {
                "acquisitionProperties": {
                    "dnsAcquisitionType": "stat",
                    "dnsServers": [
                        {
                            "addressType": "ipv4",
                            "ipv4Address": "10.1.0.250",
                            "ipv6Address": None
                        },
                        {
                            "addressType": "ipv4",
                            "ipv4Address": "10.10.0.20",
                            "ipv6Address": None
                        }
                    ]
                },
                "dhcpAcquiredDnsServers": []
            },
            "ntpProperties": {
                "acquisitionProperties": {
                    "ntpAcquisitionType": "disabled",
                    "ntpServers": None
                },
                "dhcpAcquiredNtpServers": []
            },
        },
        {
            "controllerRef": "070000000000000000000002",
            "controllerSlot": 2,
            "interfaceName": "wan0",
            "interfaceRef": "2800070000000000000000000001000000000000",
            "channel": 1,
            "alias": "creG1g-AP-b",
            "ipv4Enabled": True,
            "ipv4Address": "0.0.0.0",
            "ipv4SubnetMask": "0.0.0.0",
            "ipv4AddressConfigMethod": "configDhcp",
            "ipv4GatewayAddress": "10.1.1.1",
            "ipv6Enabled": False,
            "physicalLocation": {
                "slot": 0,
            },
            "dnsProperties": {
                "acquisitionProperties": {
                    "dnsAcquisitionType": "stat",
                    "dnsServers": [
                        {
                            "addressType": "ipv4",
                            "ipv4Address": "10.1.0.250",
                            "ipv6Address": None
                        }
                    ]
                },
                "dhcpAcquiredDnsServers": []
            },
            "ntpProperties": {
                "acquisitionProperties": {
                    "ntpAcquisitionType": "stat",
                    "ntpServers": [
                        {
                            "addrType": "ipvx",
                            "domainName": None,
                            "ipvxAddress": {
                                "addressType": "ipv4",
                                "ipv4Address": "10.13.1.5",
                                "ipv6Address": None
                            }
                        },
                        {
                            "addrType": "ipvx",
                            "domainName": None,
                            "ipvxAddress": {
                                "addressType": "ipv4",
                                "ipv4Address": "10.15.1.8",
                                "ipv6Address": None
                            }
                        }
                    ]
                },
                "dhcpAcquiredNtpServers": []
            },
        },
        {
            "controllerRef": "070000000000000000000002",
            "controllerSlot": 2,
            "interfaceName": "wan1",
            "interfaceRef": "2801070000000000000000000001000000000000",
            "channel": 2,
            "alias": "creG1g-AP-b",
            "ipv4Enabled": True,
            "ipv4Address": "0.0.0.0",
            "ipv4SubnetMask": "0.0.0.0",
            "ipv4AddressConfigMethod": "configDhcp",
            "ipv4GatewayAddress": "10.1.1.1",
            "ipv6Enabled": False,
            "physicalLocation": {
                "slot": 1,
            },
            "dnsProperties": {
                "acquisitionProperties": {
                    "dnsAcquisitionType": "stat",
                    "dnsServers": [
                        {
                            "addressType": "ipv4",
                            "ipv4Address": "10.19.1.2",
                            "ipv6Address": None
                        }
                    ]
                },
                "dhcpAcquiredDnsServers": []
            },
            "ntpProperties": {
                "acquisitionProperties": {
                    "ntpAcquisitionType": "stat",
                    "ntpServers": [
                        {
                            "addrType": "ipvx",
                            "domainName": None,
                            "ipvxAddress": {
                                "addressType": "ipv4",
                                "ipv4Address": "10.13.1.5",
                                "ipv6Address": None
                            }
                        },
                        {
                            "addrType": "ipvx",
                            "domainName": None,
                            "ipvxAddress": {
                                "addressType": "ipv4",
                                "ipv4Address": "10.15.1.18",
                                "ipv6Address": None
                            }
                        }
                    ]
                },
                "dhcpAcquiredNtpServers": []
            },
        },
    ]

    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_mgmt_interface.request'

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_controller_property_pass(self):
        """Verify dictionary return from controller property."""
        initial = {
            "state": "enable",
            "controller": "A",
            "channel": "1",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static"}
        controller_request = [
            {"physicalLocation": {"slot": 2},
             "controllerRef": "070000000000000000000002",
             "networkSettings": {"remoteAccessEnabled": True}},
            {"physicalLocation": {"slot": 1},
             "controllerRef": "070000000000000000000001",
             "networkSettings": {"remoteAccessEnabled": False}}]
        expected = {
            'A': {'controllerRef': '070000000000000000000001',
                  'controllerSlot': 1, 'ssh': False},
            'B': {'controllerRef': '070000000000000000000002',
                  'controllerSlot': 2, 'ssh': True}}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with mock.patch(self.REQ_FUNC, return_value=(200, controller_request)):
            response = mgmt_interface.controllers
            self.assertTrue(response == expected)

    def test_controller_property_fail(self):
        """Verify controllers endpoint request failure causes AnsibleFailJson exception."""
        initial = {
            "state": "enable",
            "controller": "A",
            "channel": "1",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static"}
        controller_request = [
            {"physicalLocation": {"slot": 2},
             "controllerRef": "070000000000000000000002",
             "networkSettings": {"remoteAccessEnabled": True}},
            {"physicalLocation": {"slot": 1},
             "controllerRef": "070000000000000000000001",
             "networkSettings": {"remoteAccessEnabled": False}}]
        expected = {
            'A': {'controllerRef': '070000000000000000000001',
                  'controllerSlot': 1, 'ssh': False},
            'B': {'controllerRef': '070000000000000000000002',
                  'controllerSlot': 2, 'ssh': True}}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()
        with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to retrieve the controller settings."):
            with mock.patch(self.REQ_FUNC, return_value=Exception):
                response = mgmt_interface.controllers

    def test_interface_property_match_pass(self):
        """Verify return value from interface property."""
        initial = {
            "state": "enable",
            "controller": "A",
            "channel": "1",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.0",
            "config_method": "static"}
        controller_request = [
            {"physicalLocation": {"slot": 2},
             "controllerRef": "070000000000000000000002",
             "networkSettings": {"remoteAccessEnabled": True}},
            {"physicalLocation": {"slot": 1},
             "controllerRef": "070000000000000000000001",
             "networkSettings": {"remoteAccessEnabled": False}}]
        expected = {
            "dns_servers": [{"ipv4Address": "10.1.0.250", "addressType": "ipv4"},
                            {"ipv4Address": "10.10.0.20", "addressType": "ipv4"}],
            "subnet_mask": "255.255.255.0",
            "link_status": "up",
            "ntp_servers": None,
            "ntp_config_method": "disabled",
            "controllerRef": "070000000000000000000001",
            "config_method": "configStatic",
            "enabled": True,
            "gateway": "10.1.1.1",
            "alias": "creG1g-AP-a",
            "controllerSlot": 1,
            "dns_config_method": "stat",
            "id": "2800070000000000000000000001000000000000",
            "address": "10.1.1.10",
            "ipv6Enabled": False,
            "channel": 1}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with mock.patch(self.REQ_FUNC, side_effect=[(200, self.TEST_DATA), (200, controller_request)]):
            iface = mgmt_interface.interface
            self.assertTrue(iface == expected)

    def test_interface_property_request_exception_fail(self):
        """Verify ethernet-interfaces endpoint request failure results in AnsibleFailJson exception."""
        initial = {
            "state": "enable",
            "controller": "A",
            "channel": "1",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static"}
        controller_request = [
            {"physicalLocation": {"slot": 2},
             "controllerRef": "070000000000000000000002",
             "networkSettings": {"remoteAccessEnabled": True}},
            {"physicalLocation": {"slot": 1},
             "controllerRef": "070000000000000000000001",
             "networkSettings": {"remoteAccessEnabled": False}}]

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to retrieve defined management interfaces."):
            with mock.patch(self.REQ_FUNC, side_effect=[Exception, (200, controller_request)]):
                iface = mgmt_interface.interface

    def test_interface_property_no_match_fail(self):
        """Verify return value from interface property."""
        initial = {
            "state": "enable",
            "controller": "A",
            "name": "wrong_name",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static"}
        controller_request = [
            {"physicalLocation": {"slot": 2},
             "controllerRef": "070000000000000000000002",
             "networkSettings": {"remoteAccessEnabled": True}},
            {"physicalLocation": {"slot": 1},
             "controllerRef": "070000000000000000000001",
             "networkSettings": {"remoteAccessEnabled": False}}]
        expected = {
            "dns_servers": [{"ipv4Address": "10.1.0.20", "addressType": "ipv4"},
                            {"ipv4Address": "10.1.0.50", "addressType": "ipv4"}],
            "subnet_mask": "255.255.255.0",
            "ntp_servers": None,
            "ntp_config_method": "disabled",
            "controllerRef": "070000000000000000000001",
            "config_method": "configStatic",
            "enabled": True,
            "gateway": "10.1.1.1",
            "alias": "creG1g-AP-a",
            "controllerSlot": 1,
            "dns_config_method": "stat",
            "id": "2800070000000000000000000001000000000000",
            "address": "10.1.1.111",
            "ipv6Enabled": False,
            "channel": 1}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()
        with self.assertRaisesRegexp(AnsibleFailJson, r"We could not find an interface matching"):
            with mock.patch(self.REQ_FUNC, side_effect=[(200, self.TEST_DATA), (200, controller_request)]):
                iface = mgmt_interface.interface

    def test_get_enable_interface_settings_enabled_pass(self):
        """Validate get_enable_interface_settings updates properly."""
        initial = {
            "state": "enable",
            "controller": "A",
            "name": "wrong_name",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static"}
        iface = {"enabled": False}
        expected_iface = {}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        update, expected_iface, body = mgmt_interface.get_enable_interface_settings(iface, expected_iface, False, {})
        self.assertTrue(update and expected_iface["enabled"] and body["ipv4Enabled"])

    def test_get_enable_interface_settings_disabled_pass(self):
        """Validate get_enable_interface_settings updates properly."""
        initial = {
            "state": "disable",
            "controller": "A",
            "name": "wan0",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static"}
        iface = {"enabled": True}
        expected_iface = {}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        update, expected_iface, body = mgmt_interface.get_enable_interface_settings(iface, expected_iface, False, {})
        self.assertTrue(update and not expected_iface["enabled"] and not body["ipv4Enabled"])

    def test_update_array_interface_ssh_pass(self):
        """Verify get_interface_settings gives the right static configuration response."""
        initial = {
            "state": "enable",
            "controller": "A",
            "name": "wan0",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static",
            "ssh": True}
        iface = {"dns_servers": [{"ipv4Address": "10.1.0.20", "addressType": "ipv4"},
                                 {"ipv4Address": "10.1.0.50", "addressType": "ipv4"}],
                 "subnet_mask": "255.255.255.0",
                 "link_status": "up",
                 "ntp_servers": None,
                 "ntp_config_method": "disabled",
                 "controllerRef": "070000000000000000000001",
                 "config_method": "configStatic",
                 "enabled": True,
                 "gateway": "10.1.1.1",
                 "alias": "creG1g-AP-a",
                 "controllerSlot": 1,
                 "dns_config_method": "stat",
                 "id": "2800070000000000000000000001000000000000",
                 "address": "10.1.1.111",
                 "ipv6Enabled": False,
                 "channel": 1}
        settings = {"controllerRef": "070000000000000000000001",
                    "ssh": False}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with mock.patch(self.REQ_FUNC, return_value=(200, None)):
            update = mgmt_interface.update_array(settings, iface)
            self.assertTrue(update)

    def test_update_array_dns_static_ntp_disable_pass(self):
        """Verify get_interface_settings gives the right static configuration response."""
        initial = {
            "controller": "A",
            "name": "wan0",
            "dns_config_method": "static",
            "dns_address": "192.168.1.1",
            "dns_address_backup": "192.168.1.100",
            "ntp_config_method": "disable"}
        iface = {"dns_servers": [{"ipv4Address": "10.1.0.20", "addressType": "ipv4"},
                                 {"ipv4Address": "10.1.0.50", "addressType": "ipv4"}],
                 "subnet_mask": "255.255.255.0",
                 "link_status": "up",
                 "ntp_servers": None,
                 "ntp_config_method": "disabled",
                 "controllerRef": "070000000000000000000001",
                 "config_method": "configStatic",
                 "enabled": True,
                 "gateway": "10.1.1.1",
                 "alias": "creG1g-AP-a",
                 "controllerSlot": 1,
                 "dns_config_method": "configDhcp",
                 "id": "2800070000000000000000000001000000000000",
                 "address": "10.1.1.111",
                 "ipv6Enabled": False,
                 "channel": 1}
        settings = {"controllerRef": "070000000000000000000001",
                    "ssh": False}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with mock.patch(self.REQ_FUNC, return_value=(200, None)):
            update = mgmt_interface.update_array(settings, iface)
            self.assertTrue(update)

    def test_update_array_dns_dhcp_ntp_static_pass(self):
        """Verify get_interface_settings gives the right static configuration response."""
        initial = {
            "controller": "A",
            "name": "wan0",
            "ntp_config_method": "static",
            "ntp_address": "192.168.1.1",
            "ntp_address_backup": "192.168.1.100",
            "dns_config_method": "dhcp"}
        iface = {"dns_servers": [{"ipv4Address": "10.1.0.20", "addressType": "ipv4"},
                                 {"ipv4Address": "10.1.0.50", "addressType": "ipv4"}],
                 "subnet_mask": "255.255.255.0",
                 "link_status": "up",
                 "ntp_servers": None,
                 "ntp_config_method": "disabled",
                 "controllerRef": "070000000000000000000001",
                 "config_method": "configStatic",
                 "enabled": True,
                 "gateway": "10.1.1.1",
                 "alias": "creG1g-AP-a",
                 "controllerSlot": 1,
                 "dns_config_method": "configStatic",
                 "id": "2800070000000000000000000001000000000000",
                 "address": "10.1.1.111",
                 "ipv6Enabled": False,
                 "channel": 1}
        settings = {"controllerRef": "070000000000000000000001",
                    "ssh": False}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with mock.patch(self.REQ_FUNC, return_value=(200, None)):
            update = mgmt_interface.update_array(settings, iface)
            self.assertTrue(update)

    def test_update_array_dns_dhcp_ntp_static_no_change_pass(self):
        """Verify get_interface_settings gives the right static configuration response."""
        initial = {
            "controller": "A",
            "name": "wan0",
            "ntp_config_method": "dhcp",
            "dns_config_method": "dhcp"}
        iface = {"dns_servers": [{"ipv4Address": "10.1.0.20", "addressType": "ipv4"},
                                 {"ipv4Address": "10.1.0.50", "addressType": "ipv4"}],
                 "subnet_mask": "255.255.255.0",
                 "ntp_servers": None,
                 "ntp_config_method": "dhcp",
                 "controllerRef": "070000000000000000000001",
                 "config_method": "static",
                 "enabled": True,
                 "gateway": "10.1.1.1",
                 "alias": "creG1g-AP-a",
                 "controllerSlot": 1,
                 "dns_config_method": "dhcp",
                 "id": "2800070000000000000000000001000000000000",
                 "address": "10.1.1.11",
                 "ipv6Enabled": False,
                 "channel": 1}
        settings = {"controllerRef": "070000000000000000000001",
                    "ssh": False}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with mock.patch(self.REQ_FUNC, return_value=(200, None)):
            update = mgmt_interface.update_array(settings, iface)
            self.assertFalse(update)

    def test_update_array_ipv4_ipv6_disabled_fail(self):
        """Verify exception is thrown when both ipv4 and ipv6 would be disabled at the same time."""
        initial = {
            "state": "disable",
            "controller": "A",
            "name": "wan0",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static",
            "ssh": True}
        iface = {"dns_servers": [{"ipv4Address": "10.1.0.20", "addressType": "ipv4"},
                                 {"ipv4Address": "10.1.0.50", "addressType": "ipv4"}],
                 "subnet_mask": "255.255.255.0",
                 "ntp_servers": None,
                 "ntp_config_method": "disabled",
                 "controllerRef": "070000000000000000000001",
                 "config_method": "configStatic",
                 "enabled": True,
                 "gateway": "10.1.1.1",
                 "alias": "creG1g-AP-a",
                 "controllerSlot": 1,
                 "dns_config_method": "stat",
                 "id": "2800070000000000000000000001000000000000",
                 "address": "10.1.1.11",
                 "ipv6Enabled": False,
                 "channel": 1}
        settings = {"controllerRef": "070000000000000000000001",
                    "ssh": False}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with self.assertRaisesRegexp(AnsibleFailJson, r"This storage-system already has IPv6 connectivity disabled."):
            with mock.patch(self.REQ_FUNC, return_value=(422, dict(ipv4Enabled=False, retcode="4", errorMessage=""))):
                mgmt_interface.update_array(settings, iface)

    def test_update_array_request_error_fail(self):
        """Verify exception is thrown when request results in an error."""
        initial = {
            "state": "disable",
            "controller": "A",
            "name": "wan0",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static",
            "ssh": True}
        iface = {"dns_servers": [{"ipv4Address": "10.1.0.20", "addressType": "ipv4"},
                                 {"ipv4Address": "10.1.0.50", "addressType": "ipv4"}],
                 "subnet_mask": "255.255.255.0",
                 "ntp_servers": None,
                 "ntp_config_method": "disabled",
                 "controllerRef": "070000000000000000000001",
                 "config_method": "configStatic",
                 "enabled": True,
                 "gateway": "10.1.1.1",
                 "alias": "creG1g-AP-a",
                 "controllerSlot": 1,
                 "dns_config_method": "stat",
                 "id": "2800070000000000000000000001000000000000",
                 "address": "10.1.1.111",
                 "ipv6Enabled": False,
                 "channel": 1}
        settings = {"controllerRef": "070000000000000000000001",
                    "ssh": False}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with self.assertRaisesRegexp(AnsibleFailJson, r"We failed to configure the management interface."):
            with mock.patch(self.REQ_FUNC, return_value=(300, dict(ipv4Enabled=False, retcode="4", errorMessage=""))):
                mgmt_interface.update_array(settings, iface)

    def test_update_pass(self):
        """Validate update method completes."""
        initial = {
            "state": "enable",
            "controller": "A",
            "channel": "1",
            "address": "192.168.1.1",
            "subnet_mask": "255.255.255.1",
            "config_method": "static",
            "ssh": "yes"}
        controller_request = [
            {"physicalLocation": {"slot": 2},
             "controllerRef": "070000000000000000000002",
             "networkSettings": {"remoteAccessEnabled": True}},
            {"physicalLocation": {"slot": 1},
             "controllerRef": "070000000000000000000001",
             "networkSettings": {"remoteAccessEnabled": False}}]
        expected = {
            "dns_servers": [{"ipv4Address": "10.1.0.20", "addressType": "ipv4"},
                            {"ipv4Address": "10.1.0.50", "addressType": "ipv4"}],
            "subnet_mask": "255.255.255.0",
            "ntp_servers": None,
            "ntp_config_method": "disabled",
            "controllerRef": "070000000000000000000001",
            "config_method": "configStatic",
            "enabled": True,
            "gateway": "10.1.1.1",
            "alias": "creG1g-AP-a",
            "controllerSlot": 1,
            "dns_config_method": "stat",
            "id": "2800070000000000000000000001000000000000",
            "address": "10.1.1.111",
            "ipv6Enabled": False,
            "channel": 1}

        self._set_args(initial)
        mgmt_interface = MgmtInterface()

        with self.assertRaisesRegexp(AnsibleExitJson, r"The interface settings have been updated."):
            with mock.patch(self.REQ_FUNC, side_effect=[(200, None), (200, controller_request), (200, self.TEST_DATA),
                                                        (200, controller_request), (200, self.TEST_DATA)]):
                mgmt_interface.update()

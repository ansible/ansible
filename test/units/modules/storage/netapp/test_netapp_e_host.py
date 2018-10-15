# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from mock import MagicMock

from ansible.module_utils import basic, netapp
from ansible.modules.storage.netapp import netapp_e_host
from ansible.modules.storage.netapp.netapp_e_host import Host
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type
import unittest
import mock
import pytest
import json
from units.compat.mock import patch
from ansible.module_utils._text import to_bytes


class HostTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        'api_username': 'rw',
        'api_password': 'password',
        'api_url': 'http://localhost',
        'ssid': '1',
        'name': '1',
    }
    HOST = {
        'name': '1',
        'label': '1',
        'id': '0' * 30,
        'clusterRef': 40 * '0',
        'hostTypeIndex': 28,
        'hostSidePorts': [],
        'initiators': [],
        'ports': [],
    }
    HOST_ALT = {
        'name': '2',
        'label': '2',
        'id': '1' * 30,
        'clusterRef': '1',
        'hostSidePorts': [],
        'initiators': [],
        'ports': [],
    }
    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_host.request'

    def _set_args(self, args):
        module_args = self.REQUIRED_PARAMS.copy()
        module_args.update(args)
        set_module_args(module_args)

    def test_delete_host(self):
        """Validate removing a host object"""
        self._set_args({
            'state': 'absent'
        })
        host = Host()
        with self.assertRaises(AnsibleExitJson) as result:
            # We expect 2 calls to the API, the first to retrieve the host objects defined,
            #  the second to remove the host definition.
            with mock.patch(self.REQ_FUNC, side_effect=[(200, [self.HOST]), (204, {})]) as request:
                host.apply()
        self.assertEquals(request.call_count, 2)
        # We expect the module to make changes
        self.assertEquals(result.exception.args[0]['changed'], True)

    def test_delete_host_no_changes(self):
        """Ensure that removing a host that doesn't exist works correctly."""
        self._set_args({
            'state': 'absent'
        })
        host = Host()
        with self.assertRaises(AnsibleExitJson) as result:
            # We expect a single call to the API: retrieve the defined hosts.
            with mock.patch(self.REQ_FUNC, return_value=(200, [])):
                host.apply()
        # We should not mark changed=True
        self.assertEquals(result.exception.args[0]['changed'], False)

    def test_host_exists(self):
        """Test host_exists method"""
        self._set_args({
            'state': 'absent'
        })
        host = Host()
        with mock.patch(self.REQ_FUNC, return_value=(200, [self.HOST])) as request:
            host_exists = host.host_exists
            self.assertTrue(host_exists, msg="This host should exist!")

    def test_host_exists_negative(self):
        """Test host_exists method with no matching hosts to return"""
        self._set_args({
            'state': 'absent'
        })
        host = Host()
        with mock.patch(self.REQ_FUNC, return_value=(200, [self.HOST_ALT])) as request:
            host_exists = host.host_exists
            self.assertFalse(host_exists, msg="This host should exist!")

    def test_host_exists_fail(self):
        """Ensure we do not dump a stack trace if we fail to make the request"""
        self._set_args({
            'state': 'absent'
        })
        host = Host()
        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, side_effect=Exception("http_error")) as request:
                host_exists = host.host_exists

    def test_needs_update_host_type(self):
        """Ensure a changed host_type triggers an update"""
        self._set_args({
            'state': 'present',
            'host_type': 27
        })
        host = Host()
        host.host_obj = self.HOST
        with mock.patch(self.REQ_FUNC, return_value=(200, [self.HOST])) as request:
            needs_update = host.needs_update
            self.assertTrue(needs_update, msg="An update to the host should be required!")

    def test_needs_update_cluster(self):
        """Ensure a changed group_id triggers an update"""
        self._set_args({
            'state': 'present',
            'host_type': self.HOST['hostTypeIndex'],
            'group': '1',
        })
        host = Host()
        host.host_obj = self.HOST
        with mock.patch(self.REQ_FUNC, return_value=(200, [self.HOST])) as request:
            needs_update = host.needs_update
            self.assertTrue(needs_update, msg="An update to the host should be required!")

    def test_needs_update_no_change(self):
        """Ensure no changes do not trigger an update"""
        self._set_args({
            'state': 'present',
            'host_type': self.HOST['hostTypeIndex'],
        })
        host = Host()
        host.host_obj = self.HOST
        with mock.patch(self.REQ_FUNC, return_value=(200, [self.HOST])) as request:
            needs_update = host.needs_update
            self.assertFalse(needs_update, msg="An update to the host should be required!")

    def test_needs_update_ports(self):
        """Ensure added ports trigger an update"""
        self._set_args({
            'state': 'present',
            'host_type': self.HOST['hostTypeIndex'],
            'ports': [{'label': 'abc', 'type': 'iscsi', 'port': '0'}],
        })
        host = Host()
        host.host_obj = self.HOST
        with mock.patch.object(host, 'all_hosts', [self.HOST]):
            needs_update = host.needs_update
            self.assertTrue(needs_update, msg="An update to the host should be required!")

    def test_needs_update_changed_ports(self):
        """Ensure changed ports trigger an update"""
        self._set_args({
            'state': 'present',
            'host_type': self.HOST['hostTypeIndex'],
            'ports': [{'label': 'abc', 'type': 'iscsi', 'port': '0'}],
        })
        host = Host()
        host.host_obj = self.HOST.copy()
        host.host_obj['hostSidePorts'] = [{'label': 'xyz', 'type': 'iscsi', 'port': '0', 'address': 'iqn:0'}]

        with mock.patch.object(host, 'all_hosts', [self.HOST]):
            needs_update = host.needs_update
            self.assertTrue(needs_update, msg="An update to the host should be required!")

    def test_needs_update_changed_negative(self):
        """Ensure a ports update with no changes does not trigger an update"""
        self._set_args({
            'state': 'present',
            'host_type': self.HOST['hostTypeIndex'],
            'ports': [{'label': 'abc', 'type': 'iscsi', 'port': '0'}],
        })
        host = Host()
        host.host_obj = self.HOST.copy()
        host.host_obj['hostSidePorts'] = [{'label': 'xyz', 'type': 'iscsi', 'port': '0', 'address': 'iqn:0'}]

        with mock.patch.object(host, 'all_hosts', [self.HOST]):
            needs_update = host.needs_update
            self.assertTrue(needs_update, msg="An update to the host should be required!")

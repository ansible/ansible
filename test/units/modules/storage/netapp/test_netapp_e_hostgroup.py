# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.modules.storage.netapp.netapp_e_hostgroup import NetAppESeriesHostGroup
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

try:
    from unittest import mock
except ImportError:
    import mock


class HostTest(ModuleTestCase):
    REQUIRED_PARAMS = {"api_username": "rw",
                       "api_password": "password",
                       "api_url": "http://localhost",
                       "ssid": "1"}
    REQ_FUNC = "ansible.modules.storage.netapp.netapp_e_hostgroup.NetAppESeriesHostGroup.request"
    HOSTS_GET_RESPONSE = [
        {"hostRef": "84000000600A098000A4B28D0030102E5C3DFC0F",
         "clusterRef": "85000000600A098000A4B28D0036102C5C3DFC08", "id": "84000000600A098000A4B28D0030102E5C3DFC0F",
         "name": "host1"},
        {"hostRef": "84000000600A098000A4B28D003010315C3DFC11",
         "clusterRef": "85000000600A098000A4B9D100360F765C3DFC1C", "id": "84000000600A098000A4B28D003010315C3DFC11",
         "name": "host2"},
        {"hostRef": "84000000600A098000A4B28D003010345C3DFC14",
         "clusterRef": "85000000600A098000A4B9D100360F765C3DFC1C", "id": "84000000600A098000A4B28D003010345C3DFC14",
         "name": "host3"}]
    HOSTGROUPS_GET_RESPONSE = [
        {"clusterRef": "85000000600A098000A4B28D0036102C5C3DFC08", "id": "85000000600A098000A4B28D0036102C5C3DFC08",
         "name": "group1"},
        {"clusterRef": "85000000600A098000A4B9D100360F765C3DFC1C", "id": "85000000600A098000A4B9D100360F765C3DFC1C",
         "name": "group2"},
        {"clusterRef": "85000000600A098000A4B9D100360F775C3DFC1E", "id": "85000000600A098000A4B9D100360F775C3DFC1E",
         "name": "group3"}]

    def _set_args(self, args):
        self.module_args = self.REQUIRED_PARAMS.copy()
        self.module_args.update(args)
        set_module_args(self.module_args)

    def test_hosts_fail(self):
        """Ensure that the host property method fails when self.request throws an exception."""
        self._set_args({"state": "present", "name": "hostgroup1", "hosts": ["host1", "host2"]})
        hostgroup_object = NetAppESeriesHostGroup()
        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, return_value=Exception()):
                hosts = hostgroup_object.hosts

        with mock.patch(self.REQ_FUNC, return_value=(200, [])):
            with self.assertRaisesRegexp(AnsibleFailJson, "Expected host does not exist"):
                hosts = hostgroup_object.hosts

    def test_hosts_pass(self):
        """Evaluate hosts property method for valid returned data structure."""
        expected_host_list = ['84000000600A098000A4B28D003010315C3DFC11', '84000000600A098000A4B28D0030102E5C3DFC0F']
        for hostgroup_hosts in [["host1", "host2"], ["84000000600A098000A4B28D0030102E5C3DFC0F",
                                                     "84000000600A098000A4B28D003010315C3DFC11"]]:
            self._set_args({"state": "present", "name": "hostgroup1", "hosts": hostgroup_hosts})
            hostgroup_object = NetAppESeriesHostGroup()

            with mock.patch(self.REQ_FUNC, return_value=(200, self.HOSTS_GET_RESPONSE)):
                for item in hostgroup_object.hosts:
                    self.assertTrue(item in expected_host_list)

        # Create hostgroup with no hosts
        self._set_args({"state": "present", "name": "hostgroup1"})
        hostgroup_object = NetAppESeriesHostGroup()
        with mock.patch(self.REQ_FUNC, return_value=(200, [])):
            self.assertEqual(hostgroup_object.hosts, [])

    def test_host_groups_fail(self):
        """Ensure that the host_groups property method fails when self.request throws an exception."""
        self._set_args({"state": "present", "name": "hostgroup1", "hosts": ["host1", "host2"]})
        hostgroup_object = NetAppESeriesHostGroup()
        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, return_value=Exception()):
                host_groups = hostgroup_object.host_groups

    def test_host_groups_pass(self):
        """Evaluate host_groups property method for valid return data structure."""
        expected_groups = [
            {'hosts': ['84000000600A098000A4B28D0030102E5C3DFC0F'], 'id': '85000000600A098000A4B28D0036102C5C3DFC08',
             'name': 'group1'},
            {'hosts': ['84000000600A098000A4B28D003010315C3DFC11', '84000000600A098000A4B28D003010345C3DFC14'],
             'id': '85000000600A098000A4B9D100360F765C3DFC1C', 'name': 'group2'},
            {'hosts': [], 'id': '85000000600A098000A4B9D100360F775C3DFC1E', 'name': 'group3'}]

        self._set_args({"state": "present", "name": "hostgroup1", "hosts": ["host1", "host2"]})
        hostgroup_object = NetAppESeriesHostGroup()

        with mock.patch(self.REQ_FUNC,
                        side_effect=[(200, self.HOSTGROUPS_GET_RESPONSE), (200, self.HOSTS_GET_RESPONSE)]):
            self.assertEqual(hostgroup_object.host_groups, expected_groups)

    @mock.patch.object(NetAppESeriesHostGroup, "host_groups")
    @mock.patch.object(NetAppESeriesHostGroup, "hosts")
    @mock.patch.object(NetAppESeriesHostGroup, "create_host_group")
    @mock.patch.object(NetAppESeriesHostGroup, "update_host_group")
    @mock.patch.object(NetAppESeriesHostGroup, "delete_host_group")
    def test_apply_pass(self, fake_delete_host_group, fake_update_host_group, fake_create_host_group, fake_hosts,
                        fake_host_groups):
        """Apply desired host group state to the storage array."""
        hosts_response = ['84000000600A098000A4B28D003010315C3DFC11', '84000000600A098000A4B28D0030102E5C3DFC0F']
        host_groups_response = [
            {'hosts': ['84000000600A098000A4B28D0030102E5C3DFC0F'], 'id': '85000000600A098000A4B28D0036102C5C3DFC08',
             'name': 'group1'},
            {'hosts': ['84000000600A098000A4B28D003010315C3DFC11', '84000000600A098000A4B28D003010345C3DFC14'],
             'id': '85000000600A098000A4B9D100360F765C3DFC1C', 'name': 'group2'},
            {'hosts': [], 'id': '85000000600A098000A4B9D100360F775C3DFC1E', 'name': 'group3'}]

        fake_host_groups.return_value = host_groups_response
        fake_hosts.return_value = hosts_response
        fake_create_host_group.return_value = lambda x: "Host group created!"
        fake_update_host_group.return_value = lambda x: "Host group updated!"
        fake_delete_host_group.return_value = lambda x: "Host group deleted!"

        # Test create new host group
        self._set_args({"state": "present", "name": "hostgroup1", "hosts": ["host1", "host2"]})
        hostgroup_object = NetAppESeriesHostGroup()
        with self.assertRaises(AnsibleExitJson):
            hostgroup_object.apply()

        # Test make no changes to existing host group
        self._set_args({"state": "present", "name": "group1", "hosts": ["host1"]})
        hostgroup_object = NetAppESeriesHostGroup()
        with self.assertRaises(AnsibleExitJson):
            hostgroup_object.apply()

        # Test add host to existing host group
        self._set_args({"state": "present", "name": "group1", "hosts": ["host1", "host2"]})
        hostgroup_object = NetAppESeriesHostGroup()
        with self.assertRaises(AnsibleExitJson):
            hostgroup_object.apply()

        # Test delete existing host group
        self._set_args({"state": "absent", "name": "group1"})
        hostgroup_object = NetAppESeriesHostGroup()
        with self.assertRaises(AnsibleExitJson):
            hostgroup_object.apply()

    @mock.patch.object(NetAppESeriesHostGroup, "host_groups")
    @mock.patch.object(NetAppESeriesHostGroup, "hosts")
    def test_apply_fail(self, fake_hosts, fake_host_groups):
        """Apply desired host group state to the storage array."""
        hosts_response = ['84000000600A098000A4B28D003010315C3DFC11', '84000000600A098000A4B28D0030102E5C3DFC0F']
        host_groups_response = [
            {'hosts': ['84000000600A098000A4B28D0030102E5C3DFC0F'], 'id': '85000000600A098000A4B28D0036102C5C3DFC08',
             'name': 'group1'},
            {'hosts': ['84000000600A098000A4B28D003010315C3DFC11', '84000000600A098000A4B28D003010345C3DFC14'],
             'id': '85000000600A098000A4B9D100360F765C3DFC1C', 'name': 'group2'},
            {'hosts': [], 'id': '85000000600A098000A4B9D100360F775C3DFC1E', 'name': 'group3'}]

        fake_host_groups.return_value = host_groups_response
        fake_hosts.return_value = hosts_response
        self._set_args(
            {"state": "present", "id": "84000000600A098000A4B28D0030102E5C3DFC0F", "hosts": ["host1", "host2"]})
        hostgroup_object = NetAppESeriesHostGroup()
        with self.assertRaisesRegexp(AnsibleFailJson,
                                     "The option name must be supplied when creating a new host group."):
            hostgroup_object.apply()

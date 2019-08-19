import sys

import pytest

import units.compat.unittest as unittest
from units.compat.mock import MagicMock
from units.compat.unittest import TestCase
from units.modules.utils import set_module_args


# Exoscale's cs doesn't support Python 2.6
pytestmark = []
if sys.version_info[:2] != (2, 6):
    from ansible.modules.cloud.cloudstack.cs_traffic_type import AnsibleCloudStackTrafficType, setup_module_object
    from ansible.module_utils.cloudstack import HAS_LIB_CS
    if not HAS_LIB_CS:
        pytestmark.append(pytest.mark.skip('The cloudstack library, "cs", is needed to test cs_traffic_type'))
else:
    pytestmark.append(pytest.mark.skip('Exoscale\'s cs doesn\'t support Python 2.6'))


EXISTING_TRAFFIC_TYPES_RESPONSE = {
    "count": 3,
    "traffictype": [
        {
            "id": "9801cf73-5a73-4883-97e4-fa20c129226f",
            "kvmnetworklabel": "cloudbr0",
            "physicalnetworkid": "659c1840-9374-440d-a412-55ca360c9d3c",
            "traffictype": "Management"
        },
        {
            "id": "28ed70b7-9a1f-41bf-94c3-53a9f22da8b6",
            "kvmnetworklabel": "cloudbr0",
            "physicalnetworkid": "659c1840-9374-440d-a412-55ca360c9d3c",
            "traffictype": "Guest"
        },
        {
            "id": "9c05c802-84c0-4eda-8f0a-f681364ffb46",
            "kvmnetworklabel": "cloudbr0",
            "physicalnetworkid": "659c1840-9374-440d-a412-55ca360c9d3c",
            "traffictype": "Storage"
        }
    ]
}

VALID_LIST_NETWORKS_RESPONSE = {
    "count": 1,
    "physicalnetwork": [
        {
            "broadcastdomainrange": "ZONE",
            "id": "659c1840-9374-440d-a412-55ca360c9d3c",
            "name": "eth1",
            "state": "Enabled",
            "vlan": "3900-4000",
            "zoneid": "49acf813-a8dd-4da0-aa53-1d826d6003e7"
        }
    ]
}

VALID_LIST_ZONES_RESPONSE = {
    "count": 1,
    "zone": [
        {
            "allocationstate": "Enabled",
            "dhcpprovider": "VirtualRouter",
            "dns1": "8.8.8.8",
            "dns2": "8.8.4.4",
            "guestcidraddress": "10.10.0.0/16",
            "id": "49acf813-a8dd-4da0-aa53-1d826d6003e7",
            "internaldns1": "192.168.56.1",
            "localstorageenabled": True,
            "name": "DevCloud-01",
            "networktype": "Advanced",
            "securitygroupsenabled": False,
            "tags": [],
            "zonetoken": "df20d65a-c6c8-3880-9064-4f77de2291ef"
        }
    ]
}


base_module_args = {
    "api_key": "api_key",
    "api_secret": "very_secret_content",
    "api_url": "http://localhost:8888/api/client",
    "kvm_networklabel": "cloudbr0",
    "physical_network": "eth1",
    "poll_async": True,
    "state": "present",
    "traffic_type": "Guest",
    "zone": "DevCloud-01"
}


class TestAnsibleCloudstackTraffiType(TestCase):

    def test_module_is_created_sensibly(self):
        set_module_args(base_module_args)
        module = setup_module_object()
        assert module.params['traffic_type'] == 'Guest'

    def test_update_called_when_traffic_type_exists(self):
        set_module_args(base_module_args)
        module = setup_module_object()
        actt = AnsibleCloudStackTrafficType(module)
        actt.get_traffic_type = MagicMock(return_value=EXISTING_TRAFFIC_TYPES_RESPONSE['traffictype'][0])
        actt.update_traffic_type = MagicMock()
        actt.present_traffic_type()
        self.assertTrue(actt.update_traffic_type.called)

    def test_update_not_called_when_traffic_type_doesnt_exist(self):
        set_module_args(base_module_args)
        module = setup_module_object()
        actt = AnsibleCloudStackTrafficType(module)
        actt.get_traffic_type = MagicMock(return_value=None)
        actt.update_traffic_type = MagicMock()
        actt.add_traffic_type = MagicMock()
        actt.present_traffic_type()
        self.assertFalse(actt.update_traffic_type.called)
        self.assertTrue(actt.add_traffic_type.called)

    def test_traffic_type_returned_if_exists(self):
        set_module_args(base_module_args)
        module = setup_module_object()
        actt = AnsibleCloudStackTrafficType(module)
        actt.get_physical_network = MagicMock(return_value=VALID_LIST_NETWORKS_RESPONSE['physicalnetwork'][0])
        actt.get_traffic_types = MagicMock(return_value=EXISTING_TRAFFIC_TYPES_RESPONSE)
        tt = actt.present_traffic_type()
        self.assertTrue(tt.get('kvmnetworklabel') == base_module_args['kvm_networklabel'])
        self.assertTrue(tt.get('traffictype') == base_module_args['traffic_type'])


if __name__ == '__main__':
    unittest.main()

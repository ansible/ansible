# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from units.compat import unittest

from oneview_module_loader import EthernetNetworkInfoModule
from hpe_test_utils import FactsParamsTestCase

ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test Ethernet Network",
    options=[]
)

PARAMS_GET_BY_NAME_WITH_OPTIONS = dict(
    config='config.json',
    name="Test Ethernet Network",
    options=['associatedProfiles', 'associatedUplinkGroups']
)

PRESENT_ENETS = [{
    "name": "Test Ethernet Network",
    "uri": "/rest/ethernet-networks/d34dcf5e-0d8e-441c-b00d-e1dd6a067188"
}]

ENET_ASSOCIATED_UPLINK_GROUP_URIS = [
    "/rest/uplink-sets/c6bf9af9-48e7-4236-b08a-77684dc258a5",
    "/rest/uplink-sets/e2f0031b-52bd-4223-9ac1-d91cb519d548"
]

ENET_ASSOCIATED_PROFILE_URIS = [
    "/rest/server-profiles/83e2e117-59dc-4e33-9f24-462af951cbbe",
    "/rest/server-profiles/57d3af2a-b6d2-4446-8645-f38dd808ea4d"
]

ENET_ASSOCIATED_UPLINK_GROUPS = [dict(uri=ENET_ASSOCIATED_UPLINK_GROUP_URIS[0], name='Uplink Set 1'),
                                 dict(uri=ENET_ASSOCIATED_UPLINK_GROUP_URIS[1], name='Uplink Set 2')]

ENET_ASSOCIATED_PROFILES = [dict(uri=ENET_ASSOCIATED_PROFILE_URIS[0], name='Server Profile 1'),
                            dict(uri=ENET_ASSOCIATED_PROFILE_URIS[1], name='Server Profile 2')]


class EthernetNetworkInfoSpec(unittest.TestCase,
                              FactsParamsTestCase
                              ):
    def setUp(self):
        self.configure_mocks(self, EthernetNetworkInfoModule)
        self.ethernet_networks = self.mock_ov_client.ethernet_networks
        FactsParamsTestCase.configure_client_mock(self, self.ethernet_networks)

    def test_should_get_all_enets(self):
        self.ethernet_networks.get_all.return_value = PRESENT_ENETS
        self.mock_ansible_module.params = PARAMS_GET_ALL

        EthernetNetworkInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ethernet_networks=(PRESENT_ENETS)
        )

    def test_should_get_enet_by_name(self):
        self.ethernet_networks.get_by.return_value = PRESENT_ENETS
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        EthernetNetworkInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ethernet_networks=(PRESENT_ENETS)
        )

    def test_should_get_enet_by_name_with_options(self):
        self.ethernet_networks.get_by.return_value = PRESENT_ENETS
        self.ethernet_networks.get_associated_profiles.return_value = ENET_ASSOCIATED_PROFILE_URIS
        self.ethernet_networks.get_associated_uplink_groups.return_value = ENET_ASSOCIATED_UPLINK_GROUP_URIS
        self.mock_ov_client.server_profiles.get.side_effect = ENET_ASSOCIATED_PROFILES
        self.mock_ov_client.uplink_sets.get.side_effect = ENET_ASSOCIATED_UPLINK_GROUPS

        self.mock_ansible_module.params = PARAMS_GET_BY_NAME_WITH_OPTIONS

        EthernetNetworkInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ethernet_networks=PRESENT_ENETS,
            enet_associated_profiles=ENET_ASSOCIATED_PROFILES,
            enet_associated_uplink_groups=ENET_ASSOCIATED_UPLINK_GROUPS
        )


if __name__ == '__main__':
    unittest.main()

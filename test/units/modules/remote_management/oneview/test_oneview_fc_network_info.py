# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from units.compat import unittest
from oneview_module_loader import FcNetworkInfoModule
from hpe_test_utils import FactsParamsTestCase

ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test FC Network"
)

PRESENT_NETWORKS = [{
    "name": "Test FC Network",
    "uri": "/rest/fc-networks/c6bf9af9-48e7-4236-b08a-77684dc258a5"
}]


class FcNetworkInfoSpec(unittest.TestCase,
                        FactsParamsTestCase):
    def setUp(self):
        self.configure_mocks(self, FcNetworkInfoModule)
        self.fc_networks = self.mock_ov_client.fc_networks
        FactsParamsTestCase.configure_client_mock(self, self.fc_networks)

    def test_should_get_all_fc_networks(self):
        self.fc_networks.get_all.return_value = PRESENT_NETWORKS
        self.mock_ansible_module.params = PARAMS_GET_ALL

        FcNetworkInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            fc_networks=PRESENT_NETWORKS
        )

    def test_should_get_fc_network_by_name(self):
        self.fc_networks.get_by.return_value = PRESENT_NETWORKS
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        FcNetworkInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            fc_networks=PRESENT_NETWORKS
        )


if __name__ == '__main__':
    unittest.main()

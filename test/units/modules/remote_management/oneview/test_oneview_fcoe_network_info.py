# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from units.compat import unittest

from oneview_module_loader import FcoeNetworkInfoModule

from hpe_test_utils import FactsParamsTestCase

ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test FCoE Networks"
)

PRESENT_NETWORKS = [{
    "name": "Test FCoE Networks",
    "uri": "/rest/fcoe-networks/c6bf9af9-48e7-4236-b08a-77684dc258a5"
}]


class FcoeNetworkInfoSpec(unittest.TestCase,
                          FactsParamsTestCase
                          ):
    def setUp(self):
        self.configure_mocks(self, FcoeNetworkInfoModule)
        self.fcoe_networks = self.mock_ov_client.fcoe_networks
        FactsParamsTestCase.configure_client_mock(self, self.fcoe_networks)

    def test_should_get_all_fcoe_network(self):
        self.fcoe_networks.get_all.return_value = PRESENT_NETWORKS
        self.mock_ansible_module.params = PARAMS_GET_ALL

        FcoeNetworkInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            fcoe_networks=PRESENT_NETWORKS
        )

    def test_should_get_fcoe_network_by_name(self):
        self.fcoe_networks.get_by.return_value = PRESENT_NETWORKS
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        FcoeNetworkInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            fcoe_networks=PRESENT_NETWORKS
        )


if __name__ == '__main__':
    unittest.main()

# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from units.compat import unittest
from oneview_module_loader import NetworkSetFactsModule
from hpe_test_utils import FactsParamsTestCase

ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_ALL_WITHOUT_ETHERNET = dict(
    config='config.json',
    name=None,
    options=['withoutEthernet']
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name='Network Set 1'
)

PARAMS_GET_BY_NAME_WITHOUT_ETHERNET = dict(
    config='config.json',
    name='Network Set 1',
    options=['withoutEthernet']
)


class NetworkSetFactsSpec(unittest.TestCase,
                          FactsParamsTestCase):
    def setUp(self):
        self.configure_mocks(self, NetworkSetFactsModule)
        self.network_sets = self.mock_ov_client.network_sets
        FactsParamsTestCase.configure_client_mock(self, self.network_sets)

    def test_should_get_all_network_sets(self):
        network_sets = [{
            "name": "Network Set 1",
            "networkUris": ['/rest/ethernet-networks/aaa-bbb-ccc']
        }, {
            "name": "Network Set 2",
            "networkUris": ['/rest/ethernet-networks/ddd-eee-fff', '/rest/ethernet-networks/ggg-hhh-fff']
        }]

        self.network_sets.get_all.return_value = network_sets
        self.mock_ansible_module.params = PARAMS_GET_ALL

        NetworkSetFactsModule().run()

        self.network_sets.get_all.assert_called_once_with()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(network_sets=network_sets))

    def test_should_get_all_network_sets_without_ethernet(self):
        network_sets = [{
            "name": "Network Set 1",
            "networkUris": []
        }, {
            "name": "Network Set 2",
            "networkUris": []
        }]

        self.network_sets.get_all.return_value = network_sets
        self.mock_ansible_module.params = PARAMS_GET_ALL

        NetworkSetFactsModule().run()

        self.network_sets.get_all.assert_called_once_with()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(network_sets=network_sets))

    def test_should_get_network_set_by_name(self):
        network_sets = [{
            "name": "Network Set 1",
            "networkUris": ['/rest/ethernet-networks/aaa-bbb-ccc']
        }]

        self.network_sets.get_by.return_value = network_sets
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        NetworkSetFactsModule().run()

        self.network_sets.get_by.assert_called_once_with('name', 'Network Set 1')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(network_sets=network_sets))

    def test_should_get_network_set_by_name_without_ethernet(self):
        network_sets = [{
            "name": "Network Set 1",
            "networkUris": []
        }]

        self.network_sets.get_all_without_ethernet.return_value = network_sets
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME_WITHOUT_ETHERNET

        NetworkSetFactsModule().run()

        expected_filter = "\"'name'='Network Set 1'\""
        self.network_sets.get_all_without_ethernet.assert_called_once_with(filter=expected_filter)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(network_sets=network_sets))


if __name__ == '__main__':
    unittest.main()

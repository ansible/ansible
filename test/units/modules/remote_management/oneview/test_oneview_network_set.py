# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.compat.tests import unittest, mock
from hpe_test_utils import OneViewBaseTestCase
from oneview_module_loader import NetworkSetModule

FAKE_MSG_ERROR = 'Fake message error'

NETWORK_SET = dict(
    name='OneViewSDK Test Network Set',
    networkUris=['/rest/ethernet-networks/aaa-bbb-ccc']
)

NETWORK_SET_WITH_NEW_NAME = dict(name='OneViewSDK Test Network Set - Renamed')

PARAMS_FOR_PRESENT = dict(
    config='config.json',
    state='present',
    data=dict(name=NETWORK_SET['name'],
              networkUris=['/rest/ethernet-networks/aaa-bbb-ccc'])
)

PARAMS_WITH_CHANGES = dict(
    config='config.json',
    state='present',
    data=dict(name=NETWORK_SET['name'],
              newName=NETWORK_SET['name'] + " - Renamed",
              networkUris=['/rest/ethernet-networks/aaa-bbb-ccc', 'Name of a Network'])
)

PARAMS_FOR_ABSENT = dict(
    config='config.json',
    state='absent',
    data=dict(name=NETWORK_SET['name'])
)


class NetworkSetModuleSpec(unittest.TestCase,
                           OneViewBaseTestCase):
    """
    OneViewBaseTestCase has common tests for class constructor and main function,
    also provides the mocks used in this test case.
    """

    def setUp(self):
        self.configure_mocks(self, NetworkSetModule)
        self.resource = self.mock_ov_client.network_sets
        self.ethernet_network_client = self.mock_ov_client.ethernet_networks

    def test_should_create_new_network_set(self):
        self.resource.get_by.return_value = []
        self.resource.create.return_value = NETWORK_SET

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        NetworkSetModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=NetworkSetModule.MSG_CREATED,
            ansible_facts=dict(network_set=NETWORK_SET)
        )

    def test_should_not_update_when_data_is_equals(self):
        self.resource.get_by.return_value = [NETWORK_SET]

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        NetworkSetModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=NetworkSetModule.MSG_ALREADY_PRESENT,
            ansible_facts=dict(network_set=NETWORK_SET)
        )

    def test_update_when_data_has_modified_attributes(self):
        data_merged = dict(name=NETWORK_SET['name'] + " - Renamed",
                           networkUris=['/rest/ethernet-networks/aaa-bbb-ccc',
                                        '/rest/ethernet-networks/ddd-eee-fff']
                           )

        self.resource.get_by.side_effect = [NETWORK_SET], []
        self.resource.update.return_value = data_merged
        self.ethernet_network_client.get_by.return_value = [{'uri': '/rest/ethernet-networks/ddd-eee-fff'}]

        self.mock_ansible_module.params = PARAMS_WITH_CHANGES

        NetworkSetModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=NetworkSetModule.MSG_UPDATED,
            ansible_facts=dict(network_set=data_merged)
        )

    def test_should_raise_exception_when_ethernet_network_not_found(self):
        self.resource.get_by.side_effect = [NETWORK_SET], []
        self.ethernet_network_client.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_WITH_CHANGES

        NetworkSetModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            exception=mock.ANY,
            msg=NetworkSetModule.MSG_ETHERNET_NETWORK_NOT_FOUND + "Name of a Network"
        )

    def test_should_remove_network(self):
        self.resource.get_by.return_value = [NETWORK_SET]

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        NetworkSetModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=NetworkSetModule.MSG_DELETED
        )

    def test_should_do_nothing_when_network_set_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        NetworkSetModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=NetworkSetModule.MSG_ALREADY_ABSENT
        )

    def test_update_scopes_when_different(self):
        params_to_scope = PARAMS_FOR_PRESENT.copy()
        params_to_scope['data']['scopeUris'] = ['test']
        self.mock_ansible_module.params = params_to_scope

        resource_data = NETWORK_SET.copy()
        resource_data['scopeUris'] = ['fake']
        resource_data['uri'] = 'rest/network-sets/fake'
        self.resource.get_by.return_value = [resource_data]

        patch_return = resource_data.copy()
        patch_return['scopeUris'] = ['test']
        self.resource.patch.return_value = patch_return

        NetworkSetModule().run()

        self.resource.patch.assert_called_once_with('rest/network-sets/fake',
                                                    operation='replace',
                                                    path='/scopeUris',
                                                    value=['test'])

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(network_set=patch_return),
            msg=NetworkSetModule.MSG_UPDATED
        )

    def test_should_do_nothing_when_scopes_are_the_same(self):
        params_to_scope = PARAMS_FOR_PRESENT.copy()
        params_to_scope['data']['scopeUris'] = ['test']
        self.mock_ansible_module.params = params_to_scope

        resource_data = NETWORK_SET.copy()
        resource_data['scopeUris'] = ['test']
        self.resource.get_by.return_value = [resource_data]

        NetworkSetModule().run()

        self.resource.patch.not_been_called()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(network_set=resource_data),
            msg=NetworkSetModule.MSG_ALREADY_PRESENT
        )


if __name__ == '__main__':
    unittest.main()

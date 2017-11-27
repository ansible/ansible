# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
import yaml

from ansible.compat.tests import mock
from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_datacenter import DatacenterModule
from hpe_test_utils import OneViewBaseTest

RACK_URI = '/rest/racks/rackid'

YAML_DATACENTER = """
        config: "{{ config }}"
        state: present
        data:
            name: "MyDatacenter"
            width: 5000
            depth: 6000
            contents:
                - resourceName: "Rack-221"
                  resourceUri: '/rest/racks/rackid'
                  x: 1000
                  y: 1000
          """

YAML_DATACENTER_CHANGE = """
        config: "{{ config }}"
        state: present
        data:
            name: "MyDatacenter"
            newName: "MyDatacenter1"
            width: 5000
            depth: 5000
            contents:
                - resourceUri: '/rest/racks/rackid'
                  x: 1000
                  y: 1000
      """

YAML_DATACENTER_ABSENT = """
        config: "{{ config }}"
        state: absent
        data:
            name: 'MyDatacenter'
        """

DICT_DEFAULT_DATACENTER = yaml.load(YAML_DATACENTER)["data"]
DICT_DEFAULT_DATACENTER_CHANGED = yaml.load(YAML_DATACENTER_CHANGE)["data"]


@pytest.mark.resource('datacenters')
class TestDatacenterModule(OneViewBaseTest):
    """
    OneViewBaseTest has tests for the main function and provides the mocks used in this test case.
    """

    def test_should_create_new_datacenter(self):
        self.resource.get_by.return_value = []
        self.resource.add.return_value = {"name": "name"}
        self.mock_ov_client.racks.get_by.return_value = [{'uri': RACK_URI}]

        self.mock_ansible_module.params = yaml.load(YAML_DATACENTER)

        DatacenterModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=DatacenterModule.MSG_CREATED,
            ansible_facts=dict(datacenter={"name": "name"})
        )

    def test_should_update_the_datacenter(self):
        self.resource.get_by.side_effect = [[DICT_DEFAULT_DATACENTER], []]
        self.resource.update.return_value = {"name": "name"}

        self.mock_ansible_module.params = yaml.load(YAML_DATACENTER_CHANGE)

        DatacenterModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=DatacenterModule.MSG_UPDATED,
            ansible_facts=dict(datacenter={"name": "name"})
        )

    def test_should_not_update_when_data_is_equals(self):
        datacenter_replaced = DICT_DEFAULT_DATACENTER.copy()
        del datacenter_replaced['contents'][0]['resourceName']

        self.resource.get_by.return_value = [DICT_DEFAULT_DATACENTER]
        self.mock_ov_client.racks.get_by.return_value = [{'uri': RACK_URI}]

        self.mock_ansible_module.params = yaml.load(YAML_DATACENTER)

        DatacenterModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=DatacenterModule.MSG_ALREADY_PRESENT,
            ansible_facts=dict(datacenter=DICT_DEFAULT_DATACENTER)
        )

    def test_should_remove_datacenter(self):
        self.resource.get_by.return_value = [DICT_DEFAULT_DATACENTER]

        self.mock_ansible_module.params = yaml.load(YAML_DATACENTER_ABSENT)

        DatacenterModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=DatacenterModule.MSG_DELETED
        )

    def test_should_do_nothing_when_datacenter_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(YAML_DATACENTER_ABSENT)

        DatacenterModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=DatacenterModule.MSG_ALREADY_ABSENT
        )

    def test_should_fail_when_switch_type_was_not_found(self):
        self.resource.get_by.return_value = []
        self.mock_ov_client.racks.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(YAML_DATACENTER)

        DatacenterModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(exception=mock.ANY, msg=DatacenterModule.MSG_RACK_NOT_FOUND)


if __name__ == '__main__':
    pytest.main([__file__])

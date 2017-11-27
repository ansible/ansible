# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
import yaml

from ansible.compat.tests import mock
from hpe_test_utils import OneViewBaseTest
from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_storage_system import StorageSystemModule

YAML_STORAGE_SYSTEM = """
        config: "{{ config }}"
        state: present
        data:
            credentials:
                ip_hostname: '{{ storage_system_ip_hostname }}'
                username: '{{ storage_system_username }}'
                password: '{{ storage_system_password }}'
            managedDomain: TestDomain
            managedPools:
              - domain: TestDomain
                type: StoragePoolV2
                name: CPG_FC-AO
                deviceType: FC
          """

YAML_STORAGE_SYSTEM_500 = """
        config: "{{ config }}"
        state: present
        data:
            credentials:
                username: user
                password: pass
            hostname: '10.0.0.0'
            family: StoreServ
            deviceSpecificAttributes:
                managedDomain: TestDomain
                managedPools:
                  - domain: TestDomain
                    name: CPG_FC-AO
                    deviceType: FC
          """

YAML_STORAGE_SYSTEM_BY_NAME = """
    config: "{{ config }}"
    state: present
    data:
        name: SSName
        managedDomain: TestDomain
        managedPools:
          - domain: TestDomain
            type: StoragePoolV2
            name: CPG_FC-AO
            deviceType: FC
      """

YAML_STORAGE_SYSTEM_CHANGES = """
        config: "{{ config }}"
        state: present
        data:
            credentials:
                ip_hostname: '{{ storage_system_ip_hostname }}'
                newIp_hostname: 'New IP Hostname'
                username: '{{ storage_system_username }}'
                password: '{{ storage_system_password }}'
            managedDomain: TestDomain
            managedPools:
              - domain: TestDomain
                type: StoragePoolV2
                name: CPG_FC-AO
                deviceType: FC
      """

YAML_STORAGE_SYSTEM_CHANGES_500 = """
        config: "{{ config }}"
        state: present
        data:
            credentials:
                username: '{{ storage_system_username }}'
                password: '{{ storage_system_password }}'
            hostname: '{{ storage_system_ip_hostname }}'
            newHostname: 'New IP Hostname'
            managedDomain: TestDomain
            managedPools:
              - domain: TestDomain
                name: CPG_FC-AO
                deviceType: FC
      """

YAML_STORAGE_SYSTEM_ABSENT = """
        config: "{{ config }}"
        state: absent
        data:
            credentials:
                ip_hostname: 172.18.11.12
"""

DICT_DEFAULT_STORAGE_SYSTEM = yaml.load(YAML_STORAGE_SYSTEM)["data"]
del DICT_DEFAULT_STORAGE_SYSTEM['credentials']['password']
DICT_DEFAULT_STORAGE_SYSTEM_500 = yaml.load(YAML_STORAGE_SYSTEM_500)["data"]
del DICT_DEFAULT_STORAGE_SYSTEM_500['credentials']['password']


@pytest.mark.resource('storage_systems')
class TestStorageSystemModule(OneViewBaseTest):
    def test_should_add_new_storage_system_with_credentials_from_api300(self):
        self.resource.get_by_ip_hostname.return_value = None
        self.resource.add.return_value = {"name": "name"}
        self.resource.update.return_value = {"name": "name"}

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM)

        StorageSystemModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=StorageSystemModule.MSG_ADDED,
            ansible_facts=dict(storage_system={"name": "name"})
        )

    def test_should_add_new_storage_system_with_credentials_from_api500(self):
        self.mock_ov_client.api_version = 500
        self.resource.get_by_hostname.return_value = None
        self.resource.add.return_value = {
            "deviceSpecificAttributes": {
                "discoveredPools": [
                    {
                        "name": "CPG_FC-AO",
                        "uuid": "abc-123",
                        "domain": "OtherDomain"
                    },
                    {
                        "name": "CPG_FC-AO",
                        "uuid": "def-456",
                        "domain": "TestDomain"
                    }
                ]
            }
        }
        self.resource.update.return_value = {"name": "name"}

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM_500)

        StorageSystemModule().run()

        self.resource.add.assert_called_once_with(
            {
                'username': 'user',
                'password': 'pass',
                'hostname': '10.0.0.0',
                'family': 'StoreServ'
            }
        )
        self.resource.update.assert_called_with(
            {
                'credentials': {
                    'username': 'user'
                },
                'hostname': '10.0.0.0',
                'family': 'StoreServ',
                'deviceSpecificAttributes': {
                    'managedDomain': 'TestDomain',
                    'managedPools': [{
                        'domain': 'TestDomain',
                        'name': 'CPG_FC-AO',
                        'deviceType': 'FC',
                        'uuid': 'def-456'
                    }]
                }
            }
        )

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=StorageSystemModule.MSG_ADDED,
            ansible_facts=dict(storage_system={"name": "name"})
        )

    def test_should_not_update_when_data_is_equals(self):
        self.resource.get_by_ip_hostname.return_value = DICT_DEFAULT_STORAGE_SYSTEM
        self.resource.update.return_value = {"name": "name"}

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM)

        StorageSystemModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=StorageSystemModule.MSG_ALREADY_PRESENT,
            ansible_facts=dict(storage_system=DICT_DEFAULT_STORAGE_SYSTEM)
        )

    def test_should_not_update_when_data_is_equals_using_name(self):
        dict_by_name = yaml.load(YAML_STORAGE_SYSTEM_BY_NAME)["data"]

        self.resource.get_by_name.return_value = dict_by_name

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM_BY_NAME)

        StorageSystemModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=StorageSystemModule.MSG_ALREADY_PRESENT,
            ansible_facts=dict(storage_system=dict_by_name.copy())
        )

    def test_should_fail_with_missing_required_attributes(self):
        self.mock_ansible_module.params = {
            'state': 'present',
            'config': 'config',
            'data': {
                'field': 'invalid'
            }
        }

        StorageSystemModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(exception=mock.ANY, msg=StorageSystemModule.MSG_MANDATORY_FIELDS_MISSING)

    def test_should_fail_when_credentials_attribute_is_missing(self):
        self.resource.get_by_name.return_value = []

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM_BY_NAME)

        StorageSystemModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(exception=mock.ANY, msg=StorageSystemModule.MSG_CREDENTIALS_MANDATORY)

    def test_update_when_data_has_modified_attributes(self):
        data_merged = DICT_DEFAULT_STORAGE_SYSTEM.copy()
        data_merged['credentials']['newIp_hostname'] = '10.10.10.10'

        self.resource.get_by_ip_hostname.return_value = DICT_DEFAULT_STORAGE_SYSTEM
        self.resource.update.return_value = data_merged

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM_CHANGES)

        StorageSystemModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=StorageSystemModule.MSG_UPDATED,
            ansible_facts=dict(storage_system=data_merged)
        )

    def test_update_when_data_has_modified_attributes_when_api500(self):
        self.mock_ov_client.api_version = 500
        data_merged = DICT_DEFAULT_STORAGE_SYSTEM_500.copy()
        data_merged['credentials']['newHostname'] = '10.10.10.10'

        self.resource.get_by_hostname.return_value = DICT_DEFAULT_STORAGE_SYSTEM_500
        self.resource.update.return_value = data_merged

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM_CHANGES_500)

        StorageSystemModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=StorageSystemModule.MSG_UPDATED,
            ansible_facts=dict(storage_system=data_merged)
        )

    def test_should_remove_storage_system(self):
        self.resource.get_by_ip_hostname.return_value = DICT_DEFAULT_STORAGE_SYSTEM

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM_ABSENT)

        StorageSystemModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=StorageSystemModule.MSG_DELETED
        )

    def test_should_do_nothing_when_storage_system_not_exist(self):
        self.resource.get_by_ip_hostname.return_value = []

        self.mock_ansible_module.params = yaml.load(YAML_STORAGE_SYSTEM_ABSENT)

        StorageSystemModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=StorageSystemModule.MSG_ALREADY_ABSENT
        )

if __name__ == '__main__':
    pytest.main([__file__])

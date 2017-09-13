# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy

from ansible.compat.tests import unittest, mock
from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_logical_interconnect_group import LogicalInterconnectGroupModule
from hpe_test_utils import OneViewBaseTestCase


FAKE_MSG_ERROR = 'Fake message error'

DEFAULT_LIG_NAME = 'Test Logical Interconnect Group'
RENAMED_LIG = 'Renamed Logical Interconnect Group'

DEFAULT_LIG_TEMPLATE = dict(
    name=DEFAULT_LIG_NAME,
    uplinkSets=[],
    enclosureType='C7000',
    interconnectMapTemplate=dict(
        interconnectMapEntryTemplates=[]
    )
)

PARAMS_LIG_TEMPLATE_WITH_MAP = dict(
    config='config.json',
    state='present',
    data=dict(
        name=DEFAULT_LIG_NAME,
        uplinkSets=[],
        enclosureType='C7000',
        interconnectMapTemplate=dict(
            interconnectMapEntryTemplates=[
                {
                    "logicalDownlinkUri": None,
                    "logicalLocation": {
                        "locationEntries": [
                            {
                                "relativeValue": "1",
                                "type": "Bay"
                            },
                            {
                                "relativeValue": 1,
                                "type": "Enclosure"
                            }
                        ]
                    },
                    "permittedInterconnectTypeName": "HP VC Flex-10/10D Module"
                }]
        )
    ))

PARAMS_FOR_PRESENT = dict(
    config='config.json',
    state='present',
    data=dict(name=DEFAULT_LIG_NAME)
)

PARAMS_TO_RENAME = dict(
    config='config.json',
    state='present',
    data=dict(name=DEFAULT_LIG_NAME,
              newName=RENAMED_LIG)
)

PARAMS_WITH_CHANGES = dict(
    config='config.json',
    state='present',
    data=dict(name=DEFAULT_LIG_NAME,
              description='It is an example')
)

PARAMS_FOR_ABSENT = dict(
    config='config.json',
    state='absent',
    data=dict(name=DEFAULT_LIG_NAME)
)


class LogicalInterconnectGroupGeneralSpec(unittest.TestCase,
                                          OneViewBaseTestCase):
    def setUp(self):
        self.configure_mocks(self, LogicalInterconnectGroupModule)
        self.resource = self.mock_ov_client.logical_interconnect_groups

    def test_should_create_new_lig(self):
        self.resource.get_by.return_value = []
        self.resource.create.return_value = DEFAULT_LIG_TEMPLATE

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        LogicalInterconnectGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LogicalInterconnectGroupModule.MSG_CREATED,
            ansible_facts=dict(logical_interconnect_group=DEFAULT_LIG_TEMPLATE)
        )

    def test_should_create_new_with_named_permitted_interconnect_type(self):
        self.resource.get_by.return_value = []
        self.resource.create.return_value = PARAMS_FOR_PRESENT

        self.mock_ansible_module.params = deepcopy(PARAMS_LIG_TEMPLATE_WITH_MAP)

        LogicalInterconnectGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LogicalInterconnectGroupModule.MSG_CREATED,
            ansible_facts=dict(logical_interconnect_group=PARAMS_FOR_PRESENT.copy())
        )

    def test_should_fail_when_permitted_interconnect_type_name_not_exists(self):
        self.resource.get_by.return_value = []
        self.resource.create.return_value = PARAMS_FOR_PRESENT
        self.mock_ov_client.interconnect_types.get_by.return_value = []

        self.mock_ansible_module.params = deepcopy(PARAMS_LIG_TEMPLATE_WITH_MAP)

        LogicalInterconnectGroupModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            exception=mock.ANY,
            msg=LogicalInterconnectGroupModule.MSG_INTERCONNECT_TYPE_NOT_FOUND)

    def test_should_not_update_when_data_is_equals(self):
        self.resource.get_by.return_value = [DEFAULT_LIG_TEMPLATE]

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        LogicalInterconnectGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=LogicalInterconnectGroupModule.MSG_ALREADY_PRESENT,
            ansible_facts=dict(logical_interconnect_group=DEFAULT_LIG_TEMPLATE)
        )

    def test_update_when_data_has_modified_attributes(self):
        data_merged = DEFAULT_LIG_TEMPLATE.copy()
        data_merged['description'] = 'New description'

        self.resource.get_by.return_value = [DEFAULT_LIG_TEMPLATE]
        self.resource.update.return_value = data_merged

        self.mock_ansible_module.params = PARAMS_WITH_CHANGES

        LogicalInterconnectGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LogicalInterconnectGroupModule.MSG_UPDATED,
            ansible_facts=dict(logical_interconnect_group=data_merged)
        )

    def test_rename_when_resource_exists(self):
        data_merged = DEFAULT_LIG_TEMPLATE.copy()
        data_merged['name'] = RENAMED_LIG
        params_to_rename = PARAMS_TO_RENAME.copy()

        self.resource.get_by.return_value = [DEFAULT_LIG_TEMPLATE]
        self.resource.update.return_value = data_merged

        self.mock_ansible_module.params = params_to_rename

        LogicalInterconnectGroupModule().run()

        self.resource.update.assert_called_once_with(data_merged)

    def test_create_with_newName_when_resource_not_exists(self):
        data_merged = DEFAULT_LIG_TEMPLATE.copy()
        data_merged['name'] = RENAMED_LIG
        params_to_rename = PARAMS_TO_RENAME.copy()

        self.resource.get_by.return_value = []
        self.resource.create.return_value = DEFAULT_LIG_TEMPLATE

        self.mock_ansible_module.params = params_to_rename

        LogicalInterconnectGroupModule().run()

        self.resource.create.assert_called_once_with(PARAMS_TO_RENAME['data'])

    def test_should_remove_lig(self):
        self.resource.get_by.return_value = [DEFAULT_LIG_TEMPLATE]

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        LogicalInterconnectGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LogicalInterconnectGroupModule.MSG_DELETED
        )

    def test_should_do_nothing_when_lig_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        LogicalInterconnectGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=LogicalInterconnectGroupModule.MSG_ALREADY_ABSENT
        )

    def test_update_scopes_when_different(self):
        params_to_scope = PARAMS_FOR_PRESENT.copy()
        params_to_scope['data']['scopeUris'] = ['test']
        self.mock_ansible_module.params = params_to_scope

        resource_data = DEFAULT_LIG_TEMPLATE.copy()
        resource_data['scopeUris'] = ['fake']
        resource_data['uri'] = 'rest/lig/fake'
        self.resource.get_by.return_value = [resource_data]

        patch_return = resource_data.copy()
        patch_return['scopeUris'] = ['test']
        self.resource.patch.return_value = patch_return

        LogicalInterconnectGroupModule().run()

        self.resource.patch.assert_called_once_with('rest/lig/fake',
                                                    operation='replace',
                                                    path='/scopeUris',
                                                    value=['test'])

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(logical_interconnect_group=patch_return),
            msg=LogicalInterconnectGroupModule.MSG_UPDATED
        )

    def test_should_do_nothing_when_scopes_are_the_same(self):
        params_to_scope = PARAMS_FOR_PRESENT.copy()
        params_to_scope['data']['scopeUris'] = ['test']
        self.mock_ansible_module.params = params_to_scope

        resource_data = DEFAULT_LIG_TEMPLATE.copy()
        resource_data['scopeUris'] = ['test']
        self.resource.get_by.return_value = [resource_data]

        LogicalInterconnectGroupModule().run()

        self.resource.patch.not_been_called()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(logical_interconnect_group=resource_data),
            msg=LogicalInterconnectGroupModule.MSG_ALREADY_PRESENT
        )


if __name__ == '__main__':
    unittest.main()

# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.compat.tests import unittest
from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_managed_san_facts import ManagedSanFactsModule
from hpe_test_utils import FactsParamsTestCase


class ManagedSanFactsClientConfigurationSpec(unittest.TestCase,
                                             FactsParamsTestCase):
    """
    FactsParamsTestCase has common tests for the parameters support.
    """
    ERROR_MSG = 'Fake message error'

    MANAGED_SAN_NAME = 'SAN1_0'
    MANAGED_SAN_URI = '/rest/fc-sans/managed-sans/cc64ee18-8f7d-4cdf-9bf8-a68f00e4af9c'
    MANAGED_SAN_WWN = '20:00:4A:2B:21:E0:00:01'

    PARAMS_GET_ALL = dict(
        config='config.json',
        name=None,
        wwn=None
    )

    PARAMS_GET_BY_NAME = dict(
        config='config.json',
        name=MANAGED_SAN_NAME,
        options=[]
    )

    PARAMS_GET_BY_NAME_WITH_OPTIONS = dict(
        config='config.json',
        name=MANAGED_SAN_NAME,
        options=['endpoints']
    )

    PARAMS_GET_ASSOCIATED_WWN = dict(
        config='config.json',
        name=MANAGED_SAN_NAME,
        options=[{'wwn': {'locate': MANAGED_SAN_WWN}}]
    )

    MANAGED_SAN = dict(name=MANAGED_SAN_NAME, uri=MANAGED_SAN_URI)

    ALL_MANAGED_SANS = [MANAGED_SAN,
                        dict(name='SAN1_1', uri='/rest/fc-sans/managed-sans/928374892-asd-34234234-asd23')]

    def setUp(self):
        self.configure_mocks(self, ManagedSanFactsModule)
        self.managed_sans = self.mock_ov_client.managed_sans
        FactsParamsTestCase.configure_client_mock(self, self.managed_sans)

    def test_should_get_all(self):
        self.managed_sans.get_all.return_value = self.ALL_MANAGED_SANS
        self.mock_ansible_module.params = self.PARAMS_GET_ALL

        ManagedSanFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(managed_sans=self.ALL_MANAGED_SANS)
        )

    def test_should_get_by_name(self):
        self.managed_sans.get_by_name.return_value = self.MANAGED_SAN
        self.mock_ansible_module.params = self.PARAMS_GET_BY_NAME

        ManagedSanFactsModule().run()

        self.managed_sans.get_by_name.assert_called_once_with(self.MANAGED_SAN_NAME)
        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(managed_sans=[self.MANAGED_SAN])
        )

    def test_should_get_by_name_with_options(self):
        endpoints = [dict(uri='/rest/fc-sans/endpoints/20:00:00:02:AC:00:08:E2'),
                     dict(uri='/rest/fc-sans/endpoints/20:00:00:02:AC:00:08:FF')]

        self.managed_sans.get_by_name.return_value = self.MANAGED_SAN
        self.managed_sans.get_endpoints.return_value = endpoints
        self.mock_ansible_module.params = self.PARAMS_GET_BY_NAME_WITH_OPTIONS

        ManagedSanFactsModule().run()

        self.managed_sans.get_by_name.assert_called_once_with(self.MANAGED_SAN_NAME)
        self.managed_sans.get_endpoints.assert_called_once_with(self.MANAGED_SAN_URI)
        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(managed_sans=[self.MANAGED_SAN], managed_san_endpoints=endpoints)
        )

    def test_should_get_managed_san_for_an_associated_wwn(self):
        self.managed_sans.get_by_name.return_value = self.MANAGED_SAN
        self.managed_sans.get_wwn.return_value = self.MANAGED_SAN
        self.mock_ansible_module.params = self.PARAMS_GET_ASSOCIATED_WWN

        ManagedSanFactsModule().run()

        self.managed_sans.get_wwn.assert_called_once_with(self.MANAGED_SAN_WWN)
        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(managed_sans=[self.MANAGED_SAN], wwn_associated_sans=self.MANAGED_SAN)
        )


if __name__ == '__main__':
    unittest.main()

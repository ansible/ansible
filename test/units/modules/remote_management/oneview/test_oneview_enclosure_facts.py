# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from units.compat import unittest
from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_enclosure_facts import EnclosureFactsModule
from hpe_test_utils import FactsParamsTestCase


ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test-Enclosure",
    options=[]
)

PARAMS_GET_BY_NAME_WITH_OPTIONS = dict(
    config='config.json',
    name="Test-Enclosure",
    options=['utilization', 'environmentalConfiguration', 'script']
)

PARAMS_GET_UTILIZATION_WITH_PARAMS = dict(
    config='config.json',
    name="Test-Enclosure",
    options=[dict(utilization=dict(fields='AveragePower',
                                   filter=['startDate=2016-06-30T03:29:42.000Z',
                                           'endDate=2016-07-01T03:29:42.000Z'],
                                   view='day',
                                   refresh=True))]
)

PRESENT_ENCLOSURES = [{
    "name": "Test-Enclosure",
    "uri": "/rest/enclosures/c6bf9af9-48e7-4236-b08a-77684dc258a5"
}]

ENCLOSURE_SCRIPT = '# script content'

ENCLOSURE_UTILIZATION = {
    "isFresh": "True"
}

ENCLOSURE_ENVIRONMENTAL_CONFIG = {
    "calibratedMaxPower": "2500"
}


class EnclosureFactsSpec(unittest.TestCase,
                         FactsParamsTestCase):
    def setUp(self):
        self.configure_mocks(self, EnclosureFactsModule)
        self.enclosures = self.mock_ov_client.enclosures
        FactsParamsTestCase.configure_client_mock(self, self.enclosures)

    def test_should_get_all_enclosures(self):
        self.enclosures.get_all.return_value = PRESENT_ENCLOSURES
        self.mock_ansible_module.params = PARAMS_GET_ALL

        EnclosureFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosures=(PRESENT_ENCLOSURES))
        )

    def test_should_get_enclosure_by_name(self):
        self.enclosures.get_by.return_value = PRESENT_ENCLOSURES
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        EnclosureFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosures=(PRESENT_ENCLOSURES))

        )

    def test_should_get_enclosure_by_name_with_options(self):
        self.enclosures.get_by.return_value = PRESENT_ENCLOSURES
        self.enclosures.get_script.return_value = ENCLOSURE_SCRIPT
        self.enclosures.get_utilization.return_value = ENCLOSURE_UTILIZATION
        self.enclosures.get_environmental_configuration.return_value = ENCLOSURE_ENVIRONMENTAL_CONFIG

        self.mock_ansible_module.params = PARAMS_GET_BY_NAME_WITH_OPTIONS

        EnclosureFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosures=PRESENT_ENCLOSURES,
                               enclosure_script=ENCLOSURE_SCRIPT,
                               enclosure_environmental_configuration=ENCLOSURE_ENVIRONMENTAL_CONFIG,
                               enclosure_utilization=ENCLOSURE_UTILIZATION)

        )

    def test_should_get_all_utilization_data(self):
        self.enclosures.get_by.return_value = PRESENT_ENCLOSURES
        self.enclosures.get_script.return_value = ENCLOSURE_SCRIPT
        self.enclosures.get_utilization.return_value = ENCLOSURE_UTILIZATION
        self.enclosures.get_environmental_configuration.return_value = ENCLOSURE_ENVIRONMENTAL_CONFIG

        self.mock_ansible_module.params = PARAMS_GET_BY_NAME_WITH_OPTIONS

        EnclosureFactsModule().run()

        self.enclosures.get_utilization.assert_called_once_with(PRESENT_ENCLOSURES[0]['uri'], fields='', filter='',
                                                                view='', refresh='')

    def test_should_get_utilization_with_parameters(self):
        self.enclosures.get_by.return_value = PRESENT_ENCLOSURES
        self.enclosures.get_script.return_value = ENCLOSURE_SCRIPT
        self.enclosures.get_utilization.return_value = ENCLOSURE_UTILIZATION
        self.enclosures.get_environmental_configuration.return_value = ENCLOSURE_ENVIRONMENTAL_CONFIG

        self.mock_ansible_module.params = PARAMS_GET_UTILIZATION_WITH_PARAMS

        EnclosureFactsModule().run()

        date_filter = ["startDate=2016-06-30T03:29:42.000Z", "endDate=2016-07-01T03:29:42.000Z"]

        self.enclosures.get_utilization.assert_called_once_with(
            PRESENT_ENCLOSURES[0]['uri'], fields='AveragePower', filter=date_filter, view='day', refresh=True)


if __name__ == '__main__':
    unittest.main()

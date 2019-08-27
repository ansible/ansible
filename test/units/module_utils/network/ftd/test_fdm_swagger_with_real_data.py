import json
import os
import unittest

from ansible.module_utils.network.ftd.fdm_swagger_client import FdmSwaggerValidator, FdmSwaggerParser
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_FOLDER = os.path.join(DIR_PATH, 'test_data')


class TestFdmSwagger(unittest.TestCase):

    def setUp(self):
        self.init_mock_data()

    def init_mock_data(self):
        with open(os.path.join(TEST_DATA_FOLDER, 'ngfw_with_ex.json'), 'rb') as f:
            self.base_data = json.loads(f.read().decode('utf-8'))

    def test_with_all_data(self):
        fdm_data = FdmSwaggerParser().parse_spec(self.base_data)
        validator = FdmSwaggerValidator(fdm_data)
        models = fdm_data['models']
        operations = fdm_data['operations']

        invalid = set({})
        for operation in operations:
            model_name = operations[operation]['modelName']
            method = operations[operation]['method']
            if method != 'get' and model_name in models:
                if 'example' in models[model_name]:
                    example = models[model_name]['example']
                    try:
                        valid, rez = validator.validate_data(operation, example)
                        assert valid
                    except Exception:
                        invalid.add(model_name)
        assert invalid == set(['TCPPortObject',
                               'UDPPortObject',
                               'ICMPv4PortObject',
                               'ICMPv6PortObject',
                               'StandardAccessList',
                               'ExtendedAccessList',
                               'ASPathList',
                               'RouteMap',
                               'StandardCommunityList',
                               'ExpandedCommunityList',
                               'IPV4PrefixList',
                               'IPV6PrefixList',
                               'PolicyList',
                               'SyslogServer',
                               'HAConfiguration',
                               'TestIdentitySource'])

    def test_parse_all_data(self):
        self.fdm_data = FdmSwaggerParser().parse_spec(self.base_data)
        operations = self.fdm_data['operations']
        without_model_name = []
        expected_operations_counter = 0
        for key in self.base_data['paths']:
            operation = self.base_data['paths'][key]
            for dummy in operation:
                expected_operations_counter += 1

        for key in operations:
            operation = operations[key]
            if not operation['modelName']:
                without_model_name.append(operation['url'])

            if operation['modelName'] == '_File' and 'download' not in operation['url']:
                self.fail('File type can be defined for download operation only')

        assert sorted(['/api/fdm/v2/operational/deploy/{objId}', '/api/fdm/v2/action/upgrade']) == sorted(
            without_model_name)
        assert sorted(self.fdm_data['model_operations'][None].keys()) == sorted(['deleteDeployment', 'startUpgrade'])
        assert expected_operations_counter == len(operations)

from __future__ import absolute_import

import pytest

from ansible.module_utils import basic
from ansible.module_utils.network.ftd.common import HTTPMethod, FtdConfigurationError, FtdServerError
from ansible.modules.network.ftd import ftd_configuration
from units.modules.utils import set_module_args, exit_json, fail_json, AnsibleFailJson, AnsibleExitJson

ADD_RESPONSE = {'status': 'Object added'}
EDIT_RESPONSE = {'status': 'Object edited'}
DELETE_RESPONSE = {'status': 'Object deleted'}
GET_BY_FILTER_RESPONSE = [{'name': 'foo', 'description': 'bar'}]
ARBITRARY_RESPONSE = {'status': 'Arbitrary request sent'}


class TestFtdConfiguration(object):
    module = ftd_configuration

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def operation_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_configuration.Connection')
        return connection_class_mock.return_value.get_operation_spec

    @pytest.fixture
    def resource_mock(self, mocker):
        resource_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_configuration.BaseConfigurationResource')
        resource_instance = resource_class_mock.return_value
        resource_instance.add_object.return_value = ADD_RESPONSE
        resource_instance.edit_object.return_value = EDIT_RESPONSE
        resource_instance.delete_object.return_value = DELETE_RESPONSE
        resource_instance.send_request.return_value = ARBITRARY_RESPONSE
        resource_instance.get_objects_by_filter.return_value = GET_BY_FILTER_RESPONSE
        return resource_instance

    def test_module_should_fail_without_operation_arg(self):
        set_module_args({})

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        assert 'missing required arguments: operation' in str(ex)

    def test_module_should_fail_when_no_operation_spec_found(self, operation_mock):
        operation_mock.return_value = None
        set_module_args({'operation': 'nonExistingOperation'})

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        assert 'Invalid operation name provided: nonExistingOperation' in str(ex)

    def test_module_should_add_object_when_add_operation(self, operation_mock, resource_mock):
        operation_mock.return_value = {
            'method': HTTPMethod.POST,
            'url': '/object'
        }

        params = {
            'operation': 'addObject',
            'data': {'name': 'testObject', 'type': 'object'}
        }
        result = self._run_module(params)

        assert ADD_RESPONSE == result['response']
        resource_mock.add_object.assert_called_with(operation_mock.return_value['url'], params['data'], None, None)

    def test_module_should_edit_object_when_edit_operation(self, operation_mock, resource_mock):
        operation_mock.return_value = {
            'method': HTTPMethod.PUT,
            'url': '/object/{objId}'
        }

        params = {
            'operation': 'editObject',
            'data': {'id': '123', 'name': 'testObject', 'type': 'object'},
            'path_params': {'objId': '123'}
        }
        result = self._run_module(params)

        assert EDIT_RESPONSE == result['response']
        resource_mock.edit_object.assert_called_with(operation_mock.return_value['url'], params['data'],
                                                     params['path_params'], None)

    def test_module_should_delete_object_when_delete_operation(self, operation_mock, resource_mock):
        operation_mock.return_value = {
            'method': HTTPMethod.DELETE,
            'url': '/object/{objId}'
        }

        params = {
            'operation': 'deleteObject',
            'path_params': {'objId': '123'}
        }
        result = self._run_module(params)

        assert DELETE_RESPONSE == result['response']
        resource_mock.delete_object.assert_called_with(operation_mock.return_value['url'], params['path_params'])

    def test_module_should_get_objects_by_filter_when_find_by_filter_operation(self, operation_mock, resource_mock):
        operation_mock.return_value = {
            'method': HTTPMethod.GET,
            'url': '/objects'
        }

        params = {
            'operation': 'getObjectList',
            'filters': {'name': 'foo'}
        }
        result = self._run_module(params)

        assert GET_BY_FILTER_RESPONSE == result['response']
        resource_mock.get_objects_by_filter.assert_called_with(operation_mock.return_value['url'], params['filters'],
                                                               None, None)

    def test_module_should_send_request_when_arbitrary_operation(self, operation_mock, resource_mock):
        operation_mock.return_value = {
            'method': HTTPMethod.GET,
            'url': '/object/status/{objId}'
        }

        params = {
            'operation': 'checkStatus',
            'path_params': {'objId': '123'}
        }
        result = self._run_module(params)

        assert ARBITRARY_RESPONSE == result['response']
        resource_mock.send_request.assert_called_with(operation_mock.return_value['url'], HTTPMethod.GET, None,
                                                      params['path_params'], None)

    def test_module_should_fail_when_operation_raises_configuration_error(self, operation_mock, resource_mock):
        operation_mock.return_value = {'method': HTTPMethod.GET, 'url': '/test'}
        set_module_args({'operation': 'failure'})
        resource_mock.send_request.side_effect = FtdConfigurationError('Foo error.')

        with pytest.raises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.value.args[0]
        assert result['failed']
        assert 'Failed to execute failure operation because of the configuration error: Foo error.' == result['msg']

    def test_module_should_fail_when_operation_raises_server_error(self, operation_mock, resource_mock):
        operation_mock.return_value = {'method': HTTPMethod.GET, 'url': '/test'}
        set_module_args({'operation': 'failure'})
        resource_mock.send_request.side_effect = FtdServerError({'error': 'foo'}, 500)

        with pytest.raises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.value.args[0]
        assert result['failed']
        assert 'Server returned an error trying to execute failure operation. Status code: 500. ' \
               'Server response: {\'error\': \'foo\'}' == result['msg']

    def _run_module(self, module_args):
        set_module_args(module_args)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()
        return ex.value.args[0]

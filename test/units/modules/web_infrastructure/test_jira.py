import json
import pytest

from ansible.module_utils import basic
from ansible.modules.web_infrastructure import jira
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


class FakeReader:
    def __init__(self, object):
        self.content = json.dumps(object, sort_keys=True)

    def read(self):
        return self.content


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


@pytest.fixture
def module_mock(mocker):
    return mocker.patch.multiple(basic.AnsibleModule,
                                 exit_json=exit_json,
                                 fail_json=fail_json)


@pytest.fixture
def fetch_url_mock(mocker):
    return mocker.patch('ansible.modules.web_infrastructure.jira.fetch_url')


def test_without_required_parameters(fetch_url_mock, module_mock):
    """Failure must occurs when all parameters are missing"""
    with pytest.raises(AnsibleFailJson):
        set_module_args({})
        jira.main()


def test_search_invalid_parameters(fetch_url_mock, module_mock):
    """Failure if search operation tried without jql"""
    set_module_args({
        'uri': 'test',
        'operation': 'search',
        'username': 'test',
        'password': 'test'
    })
    with pytest.raises(AnsibleFailJson):
        jira.main()


def test_basic_search(fetch_url_mock, module_mock):
    """Tests that we can search"""
    fetch_url_mock.return_value = [FakeReader({}), {'status': 200}]
    set_module_args({
        'uri': 'test',
        'operation': 'search',
        'username': 'test',
        'password': 'test',
        'jql': 'project = Test AND status = Done'
    })
    with pytest.raises(AnsibleExitJson) as result:
        jira.main()

    assert fetch_url_mock.call_count == 1
    # check we called the right url
    assert fetch_url_mock.call_args_list[0][0][1] == "test/rest/api/2/search/"
    # assert we called with the right method
    assert fetch_url_mock.call_args_list[0][1]['method'] == 'POST'
    # assert we posted the correct data. In this case, just jql
    call_data = json.loads(fetch_url_mock.call_args[1]['data'])
    assert call_data['jql'] == "project = Test AND status = Done"
    assert call_data['startAt'] == 0
    assert 'maxResults' not in call_data
    assert 'fields' not in call_data


def test_advanced_search(fetch_url_mock, module_mock):
    """Tests that we can search with all of our parameters"""
    fetch_url_mock.return_value = [FakeReader({}), {'status': 200}]
    set_module_args({
        'uri': 'test',
        'operation': 'search',
        'username': 'test',
        'password': 'test',
        'jql': 'project = Test AND status = Done',
        'searchFields': ['id', 'key'],
        'startAt': 200,
        'maxResults': 5
    })
    with pytest.raises(AnsibleExitJson) as result:
        jira.main()

    assert fetch_url_mock.call_count == 1
    # check we called the right url
    assert fetch_url_mock.call_args_list[0][0][1] == "test/rest/api/2/search/"
    # assert we called with the right method
    assert fetch_url_mock.call_args_list[0][1]['method'] == 'POST'
    # assert we posted the correct data. In this case, just jql
    call_data = json.loads(fetch_url_mock.call_args[1]['data'])
    assert call_data['jql'] == "project = Test AND status = Done"
    assert call_data['startAt'] == 200
    assert call_data['maxResults'] == 5
    assert call_data['fields'] == ['id', 'key']
    assert 'searchFields' not in call_data

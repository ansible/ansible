import collections
import mock

from ansible.modules.web_infrastructure.jenkins_plugin import JenkinsPlugin


def pass_function(*args, **kwargs):
    pass


def test__get_json_data(mocker):
    "test the json conversion of _get_url_data"

    url = 'https://api.github.com/repos/ansible/ansible'
    timeout = 30
    params = {
        'url': url,
        'timeout': timeout
    }
    module = mock.Mock()
    module.params = params

    JenkinsPlugin._csrf_enabled = pass_function
    JenkinsPlugin._get_installed_plugins = pass_function
    jenkins_plugin = JenkinsPlugin(module)

    json_data = jenkins_plugin._get_json_data(
            "{url}".format(
                url=url),
            'CSRF')

    assert isinstance(json_data, collections.Mapping)

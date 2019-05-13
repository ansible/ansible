from io import BytesIO

from ansible.modules.web_infrastructure.bugzilla import main
from ansible.module_utils.common._collections_compat import Mapping


BUG_DATA = {"uri": u'https://fake-buzilla.com',
            "username": "test",
            "password": "test"
            "response": b"""
               {
                 "id": 3638964,
                 "name": "ansible",
                 "full_name": "ansible/ansible",
              }"""
            }


def test__for_bugs(mocker):
    "test fetch bugs data"

    timeout = 30
    params = {
        'uri': BUG_DATA['uri'],
        'username': BUG_DATA['username'],
        'password': BUG_DATA['password'],
        'bug': "1234"
    }
    module = mocker.Mock()
    module.params = params

    JenkinsPlugin._csrf_enabled = pass_function
    JenkinsPlugin._get_installed_plugins = pass_function
    JenkinsPlugin._get_url_data = mocker.Mock()
    JenkinsPlugin._get_url_data.return_value = BytesIO(GITHUB_DATA['response'])
    jenkins_plugin = JenkinsPlugin(module)

    json_data = main(
        "{url}".format(url=GITHUB_DATA['url']),
        'CSRF')

    assert isinstance(json_data, Mapping)

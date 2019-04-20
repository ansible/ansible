import functools

from ansible.modules.cloud.heroku import heroku_collaborator
from units.compat import unittest
from units.compat.mock import patch, MagicMock
from units.modules.utils import AnsibleFailJson, AnsibleExitJson, ModuleTestCase, set_module_args


def check_mode_flag(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func(check_mode=True, *args, **kwargs)
        func(check_mode=False, *args, **kwargs)
    return wrapper


@patch('ansible.module_utils.heroku.HerokuHelper.check_lib')
class TestHerokuCollaboratorModule(ModuleTestCase):
    @patch('ansible.module_utils.heroku.HerokuHelper.get_heroku_client')
    def test_app_doesnt_exist(self, client_mock, *args):
        client_mock.return_value.apps.return_value = {}

        with self.assertRaises(AnsibleFailJson) as exec_info:
            set_module_args({
                'api_key': 'APIKEY',
                'user': 'max.mustermann@example.com',
                'apps': ['heroku-example-app'],
                'state': 'present',
            })
            heroku_collaborator.main()

        self.assertEqual(exec_info.exception.args[0]['msg'], 'App heroku-example-app does not exist')

    @check_mode_flag
    @patch('ansible.module_utils.heroku.HerokuHelper.get_heroku_client')
    def test_add_collaborator(self, client_mock, *args, check_mode):
        heroku_app_mock = MagicMock()
        client_mock.return_value.apps.return_value = {
            'heroku-example-app': heroku_app_mock,
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'api_key': 'APIKEY',
                'user': 'max.mustermann@example.com',
                'apps': ['heroku-example-app'],
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            heroku_collaborator.main()

        if check_mode:
            heroku_app_mock.add_collaborator.assert_not_called()
        else:
            heroku_app_mock.add_collaborator.assert_called_once_with(
                user_id_or_email='max.mustermann@example.com',
                silent=False,
            )

        self.assertEqual(exec_info.exception.args[0], {
            'changed': True,
            'msg': ['heroku-example-app'],
        })

    @check_mode_flag
    @patch('ansible.module_utils.heroku.HerokuHelper.get_heroku_client')
    def test_add_collaborator_apps_empty(self, client_mock, *args, check_mode):
        heroku_app_mock = MagicMock()
        client_mock.return_value.apps.return_value = {
            'heroku-example-app': heroku_app_mock,
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'api_key': 'APIKEY',
                'user': 'max.mustermann@example.com',
                'apps': [],
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            heroku_collaborator.main()

        heroku_app_mock.add_collaborator.assert_not_called()
        self.assertEqual(exec_info.exception.args[0], {
            'changed': False,
            'msg': [],
        })

    @check_mode_flag
    @patch('ansible.module_utils.heroku.HerokuHelper.get_heroku_client')
    def test_add_collaborator_multiple_apps(self, client_mock, *args, check_mode):
        collaborator_mock = MagicMock()
        collaborator_mock.user.email = 'max.mustermann@example.com'

        example_app_mock = MagicMock(collaborators=MagicMock(return_value=[collaborator_mock]))
        simple_app_mock = MagicMock()
        client_mock.return_value.apps.return_value = {
            'example-app': example_app_mock,
            'simple-app': simple_app_mock,
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'api_key': 'APIKEY',
                'user': 'max.mustermann@example.com',
                'apps': ['example-app', 'simple-app'],
                'suppress_invitation': True,
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            heroku_collaborator.main()

        if check_mode:
            example_app_mock.add_collaborator.assert_not_called()
            simple_app_mock.add_collaborator.assert_not_called()
        else:
            example_app_mock.add_collaborator.assert_not_called()
            simple_app_mock.add_collaborator.assert_called_once_with(
                user_id_or_email='max.mustermann@example.com',
                silent=True,
            )

        self.assertEqual(exec_info.exception.args[0], {
            'changed': True,
            'msg': ['simple-app'],
        })

    @check_mode_flag
    @patch('ansible.module_utils.heroku.HerokuHelper.get_heroku_client')
    def test_add_collaborator_exist(self, client_mock, *args, check_mode):
        collaborator_mock = MagicMock()
        collaborator_mock.user.email = 'max.mustermann@example.com'

        heroku_app_mock = MagicMock(collaborators=MagicMock(return_value=[collaborator_mock]))
        client_mock.return_value.apps.return_value = {
            'heroku-example-app': heroku_app_mock,
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'api_key': 'APIKEY',
                'user': 'max.mustermann@example.com',
                'apps': ['heroku-example-app'],
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            heroku_collaborator.main()

        heroku_app_mock.add_collaborator.assert_not_called()
        self.assertEqual(exec_info.exception.args[0], {
            'changed': False,
            'msg': [],
        })

    @check_mode_flag
    @patch('ansible.module_utils.heroku.HerokuHelper.get_heroku_client')
    def test_remove_collaborator(self, client_mock, *args, check_mode):
        collaborator_mock = MagicMock()
        collaborator_mock.user.email = 'max.mustermann@example.com'

        heroku_app_mock = MagicMock(collaborators=MagicMock(return_value=[collaborator_mock]))
        client_mock.return_value.apps.return_value = {
            'heroku-example-app': heroku_app_mock,
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'api_key': 'APIKEY',
                'user': 'max.mustermann@example.com',
                'apps': ['heroku-example-app'],
                'state': 'absent',
                '_ansible_check_mode': check_mode,
            })
            heroku_collaborator.main()

        if check_mode:
            heroku_app_mock.remove_collaborator.assert_not_called()
        else:
            heroku_app_mock.remove_collaborator.assert_called_once_with('max.mustermann@example.com')

        self.assertEqual(exec_info.exception.args[0], {
            'changed': True,
            'msg': ['heroku-example-app'],
        })

    @check_mode_flag
    @patch('ansible.module_utils.heroku.HerokuHelper.get_heroku_client')
    def test_remove_collaborator_apps_empty(self, client_mock, *args, check_mode):
        collaborator_mock = MagicMock()
        collaborator_mock.user.email = 'max.mustermann@example.com'

        heroku_app_mock = MagicMock(collaborators=MagicMock(return_value=[collaborator_mock]))
        client_mock.return_value.apps.return_value = {
            'heroku-example-app': heroku_app_mock,
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'api_key': 'APIKEY',
                'user': 'max.mustermann@example.com',
                'apps': [],
                'state': 'absent',
                '_ansible_check_mode': check_mode,
            })
            heroku_collaborator.main()

        heroku_app_mock.remove_collaborator.assert_not_called()
        self.assertEqual(exec_info.exception.args[0], {
            'changed': False,
            'msg': [],
        })

    @check_mode_flag
    @patch('ansible.module_utils.heroku.HerokuHelper.get_heroku_client')
    def test_remove_collaborator_multiple_apps(self, client_mock, *args, check_mode):
        example_collaborator_mock = MagicMock()
        example_collaborator_mock.user.email = 'max.mustermann@example.com'

        simple_collaborator_mock = MagicMock()
        simple_collaborator_mock.user.email = 'hello@example.com'

        example_app_mock = MagicMock(collaborators=MagicMock(return_value=[example_collaborator_mock]))
        simple_app_mock = MagicMock(collaborators=MagicMock(return_value=[simple_collaborator_mock]))

        client_mock.return_value.apps.return_value = {
            'example-app': example_app_mock,
            'simple-app': simple_app_mock,
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'api_key': 'APIKEY',
                'user': 'max.mustermann@example.com',
                'apps': ['simple-app', 'example-app'],
                'state': 'absent',
                '_ansible_check_mode': check_mode,
            })
            heroku_collaborator.main()

        if check_mode:
            example_app_mock.remove_collaborator.assert_not_called()
        else:
            example_app_mock.remove_collaborator.assert_called_once_with('max.mustermann@example.com')

        simple_app_mock.remove_collaborator.assert_not_called()
        self.assertEqual(exec_info.exception.args[0], {
            'changed': True,
            'msg': ['example-app'],
        })


if __name__ == '__main__':
    unittest.main()

# -*- coding: utf-8 -*-

import distutils.version

from ansible.modules.messaging.rabbitmq import rabbitmq_user
from ansible.module_utils import six
from itertools import chain

if six.PY3:
    from itertools import zip_longest
else:
    from itertools import izip_longest as zip_longest

from units.compat.mock import patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

from units.modules.messaging.rabbitmq.rabbitmq_user_fixtures import (rabbitmq_3_6_status,
                                                                     rabbitmq_3_7_status,
                                                                     rabbitmq_3_8_status)


def flatten(args):
    return [e for e in chain(*args)]


def lists_equal(l1, l2):
    return all(map(lambda t: t[0] == t[1], zip_longest(l1, l2)))


class TestRabbitMQUserModule(ModuleTestCase):
    def setUp(self):
        super(TestRabbitMQUserModule, self).setUp()
        self.module = rabbitmq_user

    def tearDown(self):
        super(TestRabbitMQUserModule, self).tearDown()

    def _assert(self, exc, attribute, expected_value, msg=''):
        value = exc.message[attribute] if hasattr(exc, attribute) else exc.args[0][attribute]
        assert value == expected_value, msg

    def test_without_required_parameters(self):
        """Failure must occur when all parameters are missing."""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._check_version')
    def test_permissions_with_same_vhost(self, _check_version, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'permissions': [{'vhost': '/'}, {'vhost': '/'}],
        })
        _check_version.return_value = distutils.version.StrictVersion('3.6.10')
        get_bin_path.return_value = '/rabbitmqctl'
        try:
            self.module.main()
        except AnsibleFailJson as e:
            self._assert(e, 'failed', True)
            self._assert(e, 'msg', "Error parsing vhost "
                                   "permissions: You can't have two permission dicts for the same vhost")

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.get')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._check_version')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.check_password')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.has_tags_modifications')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.has_permissions_modifications')
    def test_password_changes_only_when_needed(self,
                                               has_permissions_modifications,
                                               has_tags_modifications,
                                               check_password,
                                               _check_version,
                                               get,
                                               get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'update_password': 'always',
        })
        get.return_value = True
        _check_version.return_value = distutils.version.StrictVersion('3.6.10')
        get_bin_path.return_value = '/rabbitmqctl'
        check_password.return_value = True
        has_tags_modifications.return_value = False
        has_permissions_modifications.return_value = False
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', False)
            self._assert(e, 'state', 'present')

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._check_version')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.has_tags_modifications')
    def test_same_permissions_not_changing(self,
                                           has_tags_modifications,
                                           _get_permissions,
                                           _check_version,
                                           _exec,
                                           get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'permissions': [{'vhost': '/', 'configure_priv': '.*', 'write_priv': '.*', 'read_priv': '.*'}],
        })
        _get_permissions.return_value = {'/': {'read': '.*', 'write': '.*', 'configure': '.*', 'vhost': '/'}}
        _exec.return_value = 'someuser\t[]'
        _check_version.return_value = distutils.version.StrictVersion('3.6.10')
        get_bin_path.return_value = '/rabbitmqctl'
        has_tags_modifications.return_value = False
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', False)
            self._assert(e, 'state', 'present')

    @patch('ansible.module_utils.basic.AnsibleModule')
    def test_status_can_be_parsed(self, module):
        """Test correct parsing of the output of the status command."""
        module.get_bin_path.return_value = '/rabbitmqctl'
        module.check_mode = False

        versions = ['3.6.10', '3.6.16']
        for version_num in versions:
            def side_effect(args):
                assert '-q' in args
                if '--formatter' in args:
                    return 64, '', ''
                return 0, rabbitmq_3_6_status.replace('version_num', version_num), ''

            module.run_command.side_effect = side_effect
            user_controller = rabbitmq_user.RabbitMqUser(module, 'someuser', 'somepassword', list(), list(), 'rabbit')
            self.assertEqual(len(module.run_command.call_args_list), 2)
            last_call_args = flatten(module.run_command.call_args_list[-1][0])
            self.assertTrue('-q' in last_call_args)
            self.assertTrue('--formatter' not in last_call_args)
            self.assertEqual(user_controller._version, distutils.version.StrictVersion(version_num))
            module.run_command.reset_mock()

        versions = ['3.7.6', '3.7.7', '3.7.8', '3.7.9', '3.7.10', '3.7.11', '3.7.12', '3.7.13', '3.7.14', '3.7.15',
                    '3.7.16', '3.7.17', '3.7.18', '3.7.19', '3.7.20', '3.7.21', '3.7.22', '3.7.23']
        for version_num in versions:
            def side_effect(args):
                self.assertTrue('-q' in args)
                self.assertTrue('--formatter' in args)
                self.assertTrue('json' in args)
                return 0, rabbitmq_3_7_status.replace('version_num', str([ord(c) for c in version_num])), ''

            module.run_command.side_effect = side_effect
            user_controller = rabbitmq_user.RabbitMqUser(module, 'someuser', 'somepassword', list(), list(), 'rabbit')
            self.assertEqual(1, module.run_command.call_count)
            self.assertEqual(user_controller._version, distutils.version.StrictVersion(version_num))
            module.run_command.reset_mock()

        versions = ['3.8.0', '3.8.1', '3.8.2']
        for version_num in versions:
            def side_effect(args):
                self.assertTrue('-q' in args)
                self.assertTrue('--formatter' in args)
                self.assertTrue('json' in args)
                return 0, rabbitmq_3_8_status.replace('version_num', version_num), ''

            module.run_command.side_effect = side_effect
            user_controller = rabbitmq_user.RabbitMqUser(module, 'someuser', 'somepassword', list(), list(), 'rabbit')
            self.assertEqual(1, module.run_command.call_count)
            self.assertEqual(user_controller._version, distutils.version.StrictVersion(version_num))
            module.run_command.reset_mock()

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._check_version')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.has_tags_modifications')
    def test_permissions_are_fixed(self,
                                   has_tags_modifications,
                                   _get_permissions,
                                   _check_version,
                                   _exec,
                                   get_bin_path):
        """Test changes in permissions are fixed.

        Ensure that permissions that do not need to be changed are not, permissions with differences are
        fixed and permissions are cleared when needed, with the minimum number of operations. The
        permissions are fed into the module using the pre-3.7 version format.
        """
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'permissions': [
                {'vhost': '/', 'configure_priv': '.*', 'write_priv': '.*', 'read_priv': '.*'},
                {'vhost': '/ok', 'configure': '^$', 'write': '^$', 'read': '^$'}
            ],
        })
        get_bin_path.return_value = '/rabbitmqctl'
        has_tags_modifications.return_value = False
        _check_version.return_value = distutils.version.StrictVersion('3.6.10')
        _get_permissions.return_value = {
            '/wrong_vhost': {'vhost': '/wrong_vhost', 'configure': '', 'write': '', 'read': ''},
            '/ok': {'vhost': '/ok', 'configure': '^$', 'write': '^$', 'read': '^$'}
        }

        def side_effect(args):
            if 'list_users' in args:
                self.assertTrue('--formatter' not in args)
                self.assertTrue('json' not in args)
                return 'someuser\t[administrator, management]'
            if 'clear_permissions' in args:
                self.assertTrue('someuser' in args)
                self.assertTrue('/wrong_vhost' in args)
                return ''
            if 'set_permissions' in args:
                self.assertTrue('someuser' in args)
                self.assertTrue('/' in args)
                self.assertTrue(['.*', '.*', '.*'] == args[-3:])
                return ''
        _exec.side_effect = side_effect

        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', True)
            self._assert(e, 'state', 'present')
            self.assertEqual(_exec.call_count, 3)
            self.assertTrue(['clear_permissions', '-p', '/wrong_vhost', 'someuser'] ==
                            flatten(_exec.call_args_list[-2][0]))
            self.assertTrue(['set_permissions', '-p', '/', 'someuser', '.*', '.*', '.*'] ==
                            flatten(_exec.call_args_list[-1][0]))

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._check_version')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    def test_tags_are_fixed(self, _get_permissions, _check_version, _exec, get_bin_path):
        """Test user tags are fixed."""
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'tags': 'tag1,tags2',
        })
        get_bin_path.return_value = '/rabbitmqctl'
        _check_version.return_value = distutils.version.StrictVersion('3.6.10')
        _get_permissions.return_value = {'/': {'vhost': '/', 'configure': '^$', 'write': '^$', 'read': '^$'}}

        def side_effect(args):
            if 'list_users' in args:
                self.assertTrue('--formatter' not in args)
                self.assertTrue('json' not in args)
                return 'someuser\t[tag1, tag3]'
            return ''
        _exec.side_effect = side_effect

        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', True)
            self._assert(e, 'state', 'present')
            self.assertEqual(_exec.call_count, 2)
            self.assertTrue(lists_equal(['set_user_tags', 'someuser', 'tag1', 'tags2'],
                                        flatten(_exec.call_args_list[-1][0])))

    @patch('ansible.module_utils.basic.AnsibleModule')
    def test_user_json_data_can_be_parsed(self, module):
        """Ensure that user json data can be parsed.

        From version 3.7 onwards `rabbitmqctl` can output the user data in proper json format. Check that parsing
        works correctly.
        """

        def side_effect(args):
            self.assertTrue('-q' in args)
            self.assertTrue('--formatter' in args)
            self.assertTrue('json' in args)
            if 'status' in args:
                return 0, rabbitmq_3_8_status.replace('version_num', '3.8.1'), ''
            if 'list_users' in args:
                return 0, '''[
{"user":"someuser","tags":["administrator","management"]}
]''', ''
            if 'list_user_permissions' in args:
                return 0, '''[
{"vhost":"/test","configure":"^$","write":"^$","read":"^$"}
,{"vhost":"/","configure":"^$","write":"^$","read":"^$"}
]''', ''
            return 100, '', ''

        module.run_command.side_effect = side_effect
        user_controller = rabbitmq_user.RabbitMqUser(
            module, 'someuser', 'somepassword', list(),
            [{'vhost': '/', 'configure': '^$', 'write': '^$', 'read': '^$'}], 'rabbit',
            bulk_permissions=True)
        self.assertTrue(user_controller.get())
        self.assertTrue(user_controller._version, distutils.version.StrictVersion('3.8.1'))
        self.assertTrue(user_controller.existing_tags, ["administrator", "management"])
        self.assertTrue(user_controller.existing_permissions == {
            '/test': {'vhost': '/test', 'configure': '^$', 'write': '^$', 'read': '^$'},
            '/': {'vhost': '/', 'configure': '^$', 'write': '^$', 'read': '^$'}})
        self.assertEqual(module.run_command.call_count, 3)

    @patch('ansible.module_utils.basic.AnsibleModule')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._check_version')
    def test_non_bulk_permissions_are_parsed_and_set(self, _check_version, _exec, module):
        """Test that non bulk permissions are parsed correctly.

        Non-bulk permissions mean that only the permissions of the VHost specified will be changed if needed.
        If the same user has permissions in other VHosts, these will not be modified.
        """
        module.get_bin_path.return_value = '/rabbitmqctl'
        module.check_mode = False
        _check_version.return_value = distutils.version.StrictVersion('3.8.0')

        def side_effect(args):
            self.assertTrue('--formatter' in args, args)
            self.assertTrue('json' in args, args)
            if 'list_users' in args:
                return '''[
{"user":"someuser","tags":["administrator","management"]}
]'''
            if 'list_user_permissions' in args:
                self.assertTrue('someuser' in args, args)
                return '''[
{"vhost":"/test","configure":"^$","write":"^$","read":"^$"}
,{"vhost":"/","configure":"^$","write":"^$","read":"^$"}
]'''
            raise Exception('wrong command: ' + str(args))

        _exec.side_effect = side_effect
        user_controller = rabbitmq_user.RabbitMqUser(
            module, 'someuser', 'somepassword', list(), [{
                'vhost': '/',
                'configure_priv': '.*',
                'write_priv': '.*',
                'read_priv': '.*'
            }], 'rabbit'
        )
        user_controller.get()

        self.assertEqual(_exec.call_count, 2)
        self.assertListEqual(list(user_controller.existing_permissions.keys()), ['/'])
        self.assertEqual(user_controller.existing_permissions['/']['write'], '^$')
        self.assertEqual(user_controller.existing_permissions['/']['read'], '^$')
        self.assertEqual(user_controller.existing_permissions['/']['configure'], '^$')
        self.assertTrue(user_controller.has_permissions_modifications())

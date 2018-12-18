# -*- coding: utf-8 -*-

from ansible.modules.messaging.rabbitmq import rabbitmq_user
from units.compat.mock import call, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


class TestRabbitMQUserModule(ModuleTestCase):
    def setUp(self):
        super(TestRabbitMQUserModule, self).setUp()
        self.module = rabbitmq_user

    def tearDown(self):
        super(TestRabbitMQUserModule, self).tearDown()

    def _assert(self, exc, attribute, expected_value, msg=""):
        value = exc.message[attribute] if hasattr(exc, attribute) else exc.args[0][attribute]
        assert value == expected_value, msg

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing"""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    def test_permissions_with_same_vhost(self):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'permissions': [{'vhost': '/'}, {'vhost': '/'}],
        })
        with patch('ansible.module_utils.basic.AnsibleModule.get_bin_path') as get_bin_path:
            get_bin_path.return_value = '/rabbitmqctl'
            try:
                self.module.main()
            except AnsibleFailJson as e:
                self._assert(e, 'failed', True)
                self._assert(e, 'msg',
                             "Error parsing permissions: You can't have two permission dicts for the same vhost")

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.get')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.check_password')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.should_change_tags')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.has_permissions_modifications')
    def test_password_changes_only_when_needed(self, has_permissions_modifications, should_change_tags,
                                               check_password, get, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'update_password': 'always',
        })
        get.return_value = True
        get_bin_path.return_value = '/rabbitmqctl'
        check_password.return_value = True
        should_change_tags.return_value = False
        has_permissions_modifications.return_value = False
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', False)
            self._assert(e, 'state', 'present')

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.should_change_tags')
    def test_same_permissions_not_changing(self, should_change_tags, _get_permissions, _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'permissions': [{'vhost': '/', 'configure_priv': '.*', 'write_priv': '.*', 'read_priv': '.*'}],
        })
        _get_permissions.return_value = [{'vhost': '/', 'configure_priv': '.*', 'write_priv': '.*', 'read_priv': '.*'}]
        _exec.return_value = ['someuser\t[]']
        get_bin_path.return_value = '/rabbitmqctl'
        should_change_tags.return_value = False
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', False)
            self._assert(e, 'state', 'present')

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.set_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.should_change_tags')
    def test_permissions_are_fixed(self, should_change_tags, set_permissions, _get_permissions, _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'permissions': [{'vhost': '/', 'configure_priv': '.*', 'write_priv': '.*', 'read_priv': '.*'}],
        })
        set_permissions.return_value = None
        _get_permissions.return_value = []
        _exec.return_value = ['someuser\t[]']
        get_bin_path.return_value = '/rabbitmqctl'
        should_change_tags.return_value = False
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', True)
            self._assert(e, 'state', 'present')
            assert set_permissions.call_count == 1

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.set_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.should_change_tags')
    def test_permissions_are_fixed_with_different_host(self, should_change_tags, set_permissions, _get_permissions,
                                                       _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'permissions': [{'vhost': '/', 'configure_priv': '.*', 'write_priv': '.*', 'read_priv': '.*'}],
        })
        set_permissions.return_value = None
        _get_permissions.return_value = [{'vhost': 'monitoring', 'configure_priv': '.*', 'write_priv': '.*', 'read_priv': '.*'}]
        _exec.return_value = ['someuser\t[]']
        get_bin_path.return_value = '/rabbitmqctl'
        should_change_tags.return_value = False
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', True)
            self._assert(e, 'state', 'present')
            assert set_permissions.call_count == 1

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.set_tags')
    def test_tags_are_not_changed_if_empty(self, set_tags, _get_permissions, _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'tags': '',
        })
        _get_permissions.return_value = [
            {
                'vhost': '/',
                'configure_priv': '^$',
                'write_priv': '^$',
                'read_priv': '^$'
            }
        ]
        set_tags.return_value = None
        _exec.return_value = ['someuser\t[]']
        get_bin_path.return_value = '/rabbitmqctl'
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', False)
            self._assert(e, 'state', 'present')
            assert set_tags.call_count == 0

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.set_tags')
    def test_tags_are_not_changed_if_same(self, set_tags, _get_permissions, _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'tags': ' tag1,tag2 ',
        })
        _get_permissions.return_value = [
            {
                'vhost': '/',
                'configure_priv': '^$',
                'write_priv': '^$',
                'read_priv': '^$'
            }
        ]
        set_tags.return_value = None
        _exec.return_value = ['someuser\t[tag1, tag2]']
        get_bin_path.return_value = '/rabbitmqctl'
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', False)
            self._assert(e, 'state', 'present')
            assert set_tags.call_count == 0

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser.set_tags')
    def test_tags_are_not_touched(self, set_tags, _get_permissions, _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
        })
        _get_permissions.return_value = [
            {
                'vhost': '/',
                'configure_priv': '^$',
                'write_priv': '^$',
                'read_priv': '^$'
            }
        ]
        set_tags.return_value = None
        _exec.return_value = ['someuser\t[tag1, tag2]']
        get_bin_path.return_value = '/rabbitmqctl'
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', False)
            self._assert(e, 'state', 'present')
            assert set_tags.call_count == 0

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    def test_tags_are_emptied(self, _get_permissions, _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'tags': []
        })
        _get_permissions.return_value = [
            {
                'vhost': '/',
                'configure_priv': '^$',
                'write_priv': '^$',
                'read_priv': '^$'
            }
        ]
        _exec.return_value = ['someuser\t[tag1, tag2]']
        get_bin_path.return_value = '/rabbitmqctl'
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', True)
            self._assert(e, 'state', 'present')
            assert _exec.call_count == 2
            assert _exec.call_args_list == [call(['list_users'], True), call(['set_user_tags', 'someuser', ''])]

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    def test_tags_are_changed(self, _get_permissions, _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'tags': 'tag1, tag2'
        })
        _get_permissions.return_value = [
            {
                'vhost': '/',
                'configure_priv': '^$',
                'write_priv': '^$',
                'read_priv': '^$'
            }
        ]
        _exec.return_value = ['someuser\t[tag1]']
        get_bin_path.return_value = '/rabbitmqctl'
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', True)
            self._assert(e, 'state', 'present')
            assert _exec.call_count == 2
            assert _exec.call_args_list == [call(['list_users'], True),
                                            call(['set_user_tags', 'someuser', 'tag1', 'tag2'])]

    @patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._exec')
    @patch('ansible.modules.messaging.rabbitmq.rabbitmq_user.RabbitMqUser._get_permissions')
    def test_tags_passed_as_list(self, _get_permissions, _exec, get_bin_path):
        set_module_args({
            'user': 'someuser',
            'password': 'somepassword',
            'state': 'present',
            'tags': ['tag1', 'tag2']
        })
        _get_permissions.return_value = [
            {
                'vhost': '/',
                'configure_priv': '^$',
                'write_priv': '^$',
                'read_priv': '^$'
            }
        ]
        _exec.return_value = ['someuser\t[tag1]']
        get_bin_path.return_value = '/rabbitmqctl'
        try:
            self.module.main()
        except AnsibleExitJson as e:
            self._assert(e, 'changed', True)
            self._assert(e, 'state', 'present')
            assert _exec.call_count == 2
            assert _exec.call_args_list == [call(['list_users'], True),
                                            call(['set_user_tags', 'someuser', 'tag1', 'tag2'])]

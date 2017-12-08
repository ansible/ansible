import json

from ansible.modules.packaging.os import rhn_channel

from units.modules.packaging.utils import mock_request
from units.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase


class TestRhnChannel(ModuleTestCase):

    def setUp(self):
        super(TestRhnChannel, self).setUp()

        self.module = rhn_channel
        self.module.HAS_UP2DATE_CLIENT = True

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing"""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    def test_channel_already_here(self):
        """Check that result isn't changed"""
        set_module_args({
            'name': 'rhel-x86_64-server-6',
            'sysname': 'server01',
            'url': 'https://rhn.redhat.com/rpc/api',
            'user': 'user',
            'password': 'pass',
        })

        responses = [
            ('auth.login', ['X' * 43]),
            ('system.listUserSystems',
             [[{'last_checkin': '2017-08-06 19:49:52.0', 'id': '0123456789', 'name': 'server01'}]]),
            ('channel.software.listSystemChannels',
             [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
            ('auth.logout', [1]),
        ]

        with mock_request(responses, self.module.__name__):
            with self.assertRaises(AnsibleExitJson) as result:
                self.module.main()
            self.assertFalse(result.exception.args[0]['changed'])
        self.assertFalse(responses)  # all responses should have been consumed

    def test_add_channel(self):
        """Add another channel: check that result is changed"""
        set_module_args({
            'name': 'rhel-x86_64-server-6-debuginfo',
            'sysname': 'server01',
            'url': 'https://rhn.redhat.com/rpc/api',
            'user': 'user',
            'password': 'pass',
        })

        responses = [
            ('auth.login', ['X' * 43]),
            ('system.listUserSystems',
             [[{'last_checkin': '2017-08-06 19:49:52.0', 'id': '0123456789', 'name': 'server01'}]]),
            ('channel.software.listSystemChannels',
             [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
            ('channel.software.listSystemChannels',
             [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
            ('system.setChildChannels', [1]),
            ('auth.logout', [1]),
        ]

        with mock_request(responses, self.module.__name__):
            with self.assertRaises(AnsibleExitJson) as result:
                self.module.main()
            self.assertTrue(result.exception.args[0]['changed'])
        self.assertFalse(responses)  # all responses should have been consumed

    def test_remove_inexistent_channel(self):
        """Check that result isn't changed"""
        set_module_args({
            'name': 'rhel-x86_64-server-6-debuginfo',
            'state': 'absent',
            'sysname': 'server01',
            'url': 'https://rhn.redhat.com/rpc/api',
            'user': 'user',
            'password': 'pass',
        })

        responses = [
            ('auth.login', ['X' * 43]),
            ('system.listUserSystems',
             [[{'last_checkin': '2017-08-06 19:49:52.0', 'id': '0123456789', 'name': 'server01'}]]),
            ('channel.software.listSystemChannels',
             [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
            ('auth.logout', [1]),
        ]

        with mock_request(responses, self.module.__name__):
            with self.assertRaises(AnsibleExitJson) as result:
                self.module.main()
            self.assertFalse(result.exception.args[0]['changed'])
        self.assertFalse(responses)  # all responses should have been consumed

    def test_remove_channel(self):
        """Check that result isn't changed"""
        set_module_args({
            'name': 'rhel-x86_64-server-6-debuginfo',
            'state': 'absent',
            'sysname': 'server01',
            'url': 'https://rhn.redhat.com/rpc/api',
            'user': 'user',
            'password': 'pass',
        })

        responses = [
            ('auth.login', ['X' * 43]),
            ('system.listUserSystems',
             [[{'last_checkin': '2017-08-06 19:49:52.0', 'id': '0123456789', 'name': 'server01'}]]),
            ('channel.software.listSystemChannels', [[
                {'channel_name': 'RHEL Server Debuginfo (v.6 for x86_64)', 'channel_label': 'rhel-x86_64-server-6-debuginfo'},
                {'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}
            ]]),
            ('channel.software.listSystemChannels', [[
                {'channel_name': 'RHEL Server Debuginfo (v.6 for x86_64)', 'channel_label': 'rhel-x86_64-server-6-debuginfo'},
                {'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}
            ]]),
            ('system.setChildChannels', [1]),
            ('auth.logout', [1]),
        ]

        with mock_request(responses, self.module.__name__):
            with self.assertRaises(AnsibleExitJson) as result:
                self.module.main()
            self.assertTrue(result.exception.args[0]['changed'])
        self.assertFalse(responses)  # all responses should have been consumed

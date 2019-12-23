
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from units.compat.mock import patch
from ansible.modules.notification import campfire
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


class TestCampfireModule(ModuleTestCase):

    def setUp(self):
        super(TestCampfireModule, self).setUp()
        self.module = campfire

    def tearDown(self):
        super(TestCampfireModule, self).tearDown()

    @pytest.fixture
    def fetch_url_mock(self, mocker):
        return mocker.patch('ansible.module_utils.notification.campfire.fetch_url')

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing"""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    def test_successful_message(self):
        """Test failure message"""
        set_module_args({
            'subscription': 'test',
            'token': 'abc',
            'room': 'test',
            'msg': 'test'
        })

        with patch.object(campfire, "fetch_url") as fetch_url_mock:
            fetch_url_mock.return_value = (None, {"status": 200})
            with self.assertRaises(AnsibleExitJson):
                self.module.main()

            assert fetch_url_mock.call_count == 1
            url = fetch_url_mock.call_args[0][1]
            data = fetch_url_mock.call_args[1]['data']

            assert url == 'https://test.campfirenow.com/room/test/speak.xml'
            assert data == '<message><body>test</body></message>'

    def test_successful_message_with_notify(self):
        """Test failure message"""
        set_module_args({
            'subscription': 'test',
            'token': 'abc',
            'room': 'test',
            'msg': 'test',
            'notify': 'bell'
        })

        with patch.object(campfire, "fetch_url") as fetch_url_mock:
            fetch_url_mock.return_value = (None, {"status": 200})
            with self.assertRaises(AnsibleExitJson):
                self.module.main()

            assert fetch_url_mock.call_count == 2
            notify_call = fetch_url_mock.mock_calls[0]
            url = notify_call[1][1]
            data = notify_call[2]['data']

            assert url == 'https://test.campfirenow.com/room/test/speak.xml'
            assert data == '<message><type>SoundMessage</type><body>bell</body></message>'

            message_call = fetch_url_mock.mock_calls[1]
            url = message_call[1][1]
            data = message_call[2]['data']

            assert url == 'https://test.campfirenow.com/room/test/speak.xml'
            assert data == '<message><body>test</body></message>'

    def test_failure_message(self):
        """Test failure message"""
        set_module_args({
            'subscription': 'test',
            'token': 'abc',
            'room': 'test',
            'msg': 'test'
        })

        with patch.object(campfire, "fetch_url") as fetch_url_mock:
            fetch_url_mock.return_value = (None, {"status": 403})
            with self.assertRaises(AnsibleFailJson):
                self.module.main()

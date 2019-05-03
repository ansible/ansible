import json
import pytest
from units.compat.mock import patch
from ansible.modules.notification import ms_teams
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


class TestMsTeamsModule(ModuleTestCase):

    def setUp(self):
        super(TestSlackModule, self).setUp()
        self.module = slack

    def tearDown(self):
        super(TestSlackModule, self).tearDown()

    @pytest.fixture
    def fetch_url_mock(self, mocker):
        return mocker.patch('ansible.module_utils.notification.slack.fetch_url')

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing"""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    def test_sucessful_message(self):
        """tests sending a message"""
        set_module_args({
            'body': 'Hello Teams!',
            'subject': 'I am the subject',
            'webhook': 'https://outlook.office.com/my-webhook'
        })

        with patch.object(slack, "fetch_url") as fetch_url_mock:
            fetch_url_mock.return_value = (None, {"status": 200})
            with self.assertRaises(AnsibleExitJson):
                self.module.main()

            self.assertTrue(fetch_url_mock.call_count, 1)
            assert fetch_url_mock.call_args[1]['url'] == 'https://outlook.office.com/my-webhook'

            call_data = json.loads(fetch_url_mock.call_args[1]['data'])
            assert call_data['text'] == "Hello Teams!"
            assert call_data['title'] == "I am the subject"
            assert call_data['themeColor'] == "ffffcc"

    def test_failed_message(self):
        """tests failing to send a message"""

        set_module_args({
            'body': 'Hello Teams!',
            'subject': 'I am the subject',
            'webhook': 'https://outlook.office.com/my-webhook'
        })

        with patch.object(slack, "fetch_url") as fetch_url_mock:
            fetch_url_mock.return_value = (None, {"status": 400, 'msg': 'test'})
            with self.assertRaises(AnsibleFailJson):
                self.module.main()

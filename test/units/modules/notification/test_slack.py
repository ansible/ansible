import json
import pytest
from units.compat.mock import patch
from ansible.modules.notification import slack
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


class TestSlackModule(ModuleTestCase):

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

    def test_invalid_old_token(self):
        """Failure if there is an old style token"""
        set_module_args({
            'token': 'test',
        })
        with self.assertRaises(AnsibleFailJson):
            self.module.main()

    def test_sucessful_message(self):
        """tests sending a message. This is example 1 from the docs"""
        set_module_args({
            'token': 'XXXX/YYYY/ZZZZ',
            'msg': 'test'
        })

        with patch.object(slack, "fetch_url") as fetch_url_mock:
            fetch_url_mock.return_value = (None, {"status": 200})
            with self.assertRaises(AnsibleExitJson):
                self.module.main()

            self.assertTrue(fetch_url_mock.call_count, 1)
            call_data = json.loads(fetch_url_mock.call_args[1]['data'])
            assert call_data['username'] == "Ansible"
            assert call_data['text'] == "test"
            assert fetch_url_mock.call_args[1]['url'] == "https://hooks.slack.com/services/XXXX/YYYY/ZZZZ"

    def test_failed_message(self):
        """tests failing to send a message"""

        set_module_args({
            'token': 'XXXX/YYYY/ZZZZ',
            'msg': 'test'
        })

        with patch.object(slack, "fetch_url") as fetch_url_mock:
            fetch_url_mock.return_value = (None, {"status": 404, 'msg': 'test'})
            with self.assertRaises(AnsibleFailJson):
                self.module.main()

    def test_message_with_thread(self):
        """tests sending a message with a thread"""
        set_module_args({
            'token': 'XXXX/YYYY/ZZZZ',
            'msg': 'test',
            'thread_id': 100.00
        })

        with patch.object(slack, "fetch_url") as fetch_url_mock:
            fetch_url_mock.return_value = (None, {"status": 200})
            with self.assertRaises(AnsibleExitJson):
                self.module.main()

            self.assertTrue(fetch_url_mock.call_count, 1)
            call_data = json.loads(fetch_url_mock.call_args[1]['data'])
            assert call_data['username'] == "Ansible"
            assert call_data['text'] == "test"
            assert call_data['thread_ts'] == 100.00
            assert fetch_url_mock.call_args[1]['url'] == "https://hooks.slack.com/services/XXXX/YYYY/ZZZZ"

    def test_message_with_invalid_color(self):
        """tests sending invalid color value to module"""
        set_module_args({
            'token': 'XXXX/YYYY/ZZZZ',
            'msg': 'test',
            'color': 'aa',
        })
        with self.assertRaises(AnsibleFailJson) as exec_info:
            self.module.main()

        msg = "Color value specified should be either one of" \
              " ['normal', 'good', 'warning', 'danger'] or any valid" \
              " hex value with length 3 or 6."
        assert exec_info.exception.args[0]['msg'] == msg


color_test = [
    ('#111111', True),
    ('#00aabb', True),
    ('#abc', True),
    ('#gghhjj', False),
    ('#ghj', False),
    ('#a', False),
    ('#aaaaaaaa', False),
    ('', False),
    ('aaaa', False),
    ('$00aabb', False),
    ('$00a', False),
]


@pytest.mark.parametrize("color_value, ret_status", color_test)
def test_is_valid_hex_color(color_value, ret_status):
    generated_value = slack.is_valid_hex_color(color_value)
    assert generated_value == ret_status

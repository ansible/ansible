import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.modules.messaging import kafka_topics


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

    
class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)
    

class TestKafka(unittest.TestCase):
    
    def setUp(self):
        self.mock_exit_fail = patch.multiple(basic.AnsibleModule,
                                             exit_json=exit_json,
                                             fail_json=fail_json)
        self.mock_exit_fail.start()
        self.addCleanup(self.mock_exit_fail.stop)

    def tearDown(self):
        pass

    def test_kafka_topics(self):
        set_module_args({
            'topic': 'jambon',
            'zookeeper': 'carotte.localhost:2181',
            'describe': True,
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "__consumer_offsets\\\\njambon\\\\nfromage\\\\ntartiflette\\\\n"
            stderr = "[2017-09-15 15:33:35,307] ERROR org.apache.kafka.common.errors.InvalidTopicException: topic name tes@@#(23 is illegal, contains a character other than ASCII alphanumerics, '.', '_' and '-'\\\\n (kafka.admin.TopicCommand$)\\\\n"
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_topics.main()
            self.assertFalse(result.exception.args[0]['changed'])

        self.assertEqual(mock_run_command.call_count, 1)
        self.assertEqual(mock_run_command.call_args[0][0][0], '/usr/bin/kafka-configs')

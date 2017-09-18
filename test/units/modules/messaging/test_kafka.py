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


def get_bin_path(self, arg, required=False):
    if arg.endswith('kafka-topics'):
        return '/usr/bin/kafka-topics'
    else:
        if required:
            fail_json(msg='%r not found !' % arg)


class TestKafka(unittest.TestCase):

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json,
                                                 get_bin_path=get_bin_path)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def tearDown(self):
        pass

    def test_kafka_topics_list_specific(self):
        set_module_args({
            'executable': None,
            'topic': 'jambon',
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "jambon\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_topics.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-topics --list --zookeeper carotte.localhost:2181 --topic jambon')

    def test_kafka_topics_list_all(self):
        set_module_args({
            'executable': None,
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "__consumer_offsets\\\\njambon\\\\nfromage\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_topics.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-topics --list --zookeeper carotte.localhost:2181')

    def test_kafka_topics_create(self):
        set_module_args({
            'executable': None,
            'topic': 'jambon',
            'action': 'create',
            'replication_factor': '1',
            'partitions': '2',
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Created topic \\\"jambon\\\".\\\\n"
            stderr = "[2017-09-15 15:33:35,307] " + \
                "ERROR org.apache.kafka.common.errors.InvalidTopicException: " + \
                "topic name tes@@#(23 is illegal, contains a character other " + \
                "than ASCII alphanumerics, '.', '_' and '-'\\\\n (kafka.admin.TopicCommand$)\\\\n"
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_topics.main()
            self.assertTrue(result.exception.args[0]['changed'])

    def test_kafka_topics_delete(self):
        set_module_args({
            'executable': None,
            'topic': 'jambon',
            'action': 'delete',
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Topic jambon is marked for deletion.\\\\n" + \
                "Note: This will have no impact if " + \
                "delete.topic.enable is not set to true.\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_topics.main()
            self.assertTrue(result.exception.args[0]['changed'])
        mock_run_command.assert_called_once_with('/usr/bin/kafka-topics --delete --zookeeper carotte.localhost:2181 --topic jambon --if-exists')

    def test_kafka_topics_describe_specific(self):
        set_module_args({
            'executable': None,
            'topic': 'jambon',
            'action': 'describe',
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Topic:jambon\\\\tPartitionCount:2\\\\t" + \
                "ReplicationFactor:1\\\\t" + \
                "Configs:compression.type=gzip,cleanup.policy=delete\\\\n\\\\t" + \
                "Topic: jambon\\\\tPartition: 0\\\\tLeader: 2\\\\t" + \
                "Replicas: 2\\\\tIsr: 2\\\\n\\\\t" + \
                "Topic: jambon\\\\tPartition: 1\\\\tLeader: 3\\\\tReplicas: 3\\\\tIsr: 3\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_topics.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-topics --describe --zookeeper carotte.localhost:2181 --topic jambon')

    def test_kafka_topics_describe_all(self):
        set_module_args({
            'executable': None,
            'action': 'describe',
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Topic:__consumer_offsets\\\\tPartitionCount:2\\\\t" + \
                "ReplicationFactor:1\\\\t" + \
                "Configs:\\\\t" + \
                "Topic: __consumer_offsets\\\\tPartition: 0\\\\tLeader: 2\\\\t" + \
                "Replicas: 2\\\\tIsr: 2\\\\n\\\\tTopic: __consumer_offsets\\\\t" + \
                "Partition: 1\\\\tLeader: 3\\\\tReplicas: 3\\\\tIsr: 3\\\\n" + \
                "ReplicationFactor:1\\\\t" + \
                "Topic:jambon\\\\tPartitionCount:2\\\\t" + \
                "Configs:compression.type=gzip,cleanup.policy=delete\\\\n\\\\t" + \
                "Topic: jambon\\\\tPartition: 0\\\\tLeader: 2\\\\t" + \
                "Replicas: 2\\\\tIsr: 2\\\\n\\\\t" + \
                "Topic: jambon\\\\tPartition: 1\\\\tLeader: 3\\\\tReplicas: 3\\\\tIsr: 3\\\\n" + \
                "Topic:fromage\\\\tPartitionCount:2\\\\t" + \
                "Configs:compression.type=gzip\\\\n\\\\t" + \
                "Topic: fromage\\\\tPartition: 0\\\\tLeader: 2\\\\t" + \
                "Replicas: 2\\\\tIsr: 2\\\\n\\\\t" + \
                "Topic: fromage\\\\tPartition: 1\\\\tLeader: 3\\\\tReplicas: 3\\\\tIsr: 3\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_topics.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-topics --describe --zookeeper carotte.localhost:2181')

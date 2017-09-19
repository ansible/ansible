import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.modules.messaging import kafka_configs


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
    elif arg.endswith('kafka-configs'):
        return '/usr/bin/kafka-configs'
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

    def test_kafka_configs_describe_one(self):
        set_module_args({
            'executable': None,
            'entity_type': 'topics',
            'entity_name': 'georgette',
            'zookeeper': 'carotte.localhost:2181',
            'describe': True,
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Configs for topic 'test-GDE' are " + \
                "cleanup.policy=delete,compression.type=gzip,flush.ms=1000\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_configs.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-configs --describe '
                                                 '--zookeeper carotte.localhost:2181 '
                                                 '--entity-type topics '
                                                 '--entity-name georgette')

    def test_kafka_configs_describe_all(self):
        set_module_args({
            'executable': None,
            'entity_type': 'topics',
            'zookeeper': 'carotte.localhost:2181',
            'describe': True,
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Configs for topic 'georgette' are " + \
                "cleanup.policy=delete,compression.type=gzip,flush.ms=1000\\\\n" + \
                "Configs for topic '__consumer_offsets' are " + \
                "segment.bytes=104857600,cleanup.policy=compact\\\\n" + \
                "Configs for topic 'admin-filtrage-topic' are \\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_configs.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-configs --describe '
                                                 '--zookeeper carotte.localhost:2181 '
                                                 '--entity-type topics')

    def test_kafka_configs_add_config(self):
        set_module_args({
            'executable': None,
            'entity_type': 'topics',
            'entity_name': 'georgette',
            'configs': {'cleanup.policy': 'delete', 'compression.type': 'gzip'},
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Updated config for entity: topics 'georgette'"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_configs.main()
            self.assertTrue(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-configs --alter '
                                                 '--zookeeper carotte.localhost:2181 '
                                                 '--entity-type topics '
                                                 '--entity-name georgette '
                                                 '--add-config cleanup.policy=delete,'
                                                 'compression.type=gzip')

    def test_kafka_configs_add_config_no_change(self):
        set_module_args({
            'executable': None,
            'entity_type': 'topics',
            'entity_name': 'georgette',
            'configs': {'cleanup.policy': 'delete', 'compression.type': 'gzip'},
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Nothing to do for config entity: topics 'georgette'"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_configs.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-configs --alter '
                                                 '--zookeeper carotte.localhost:2181 '
                                                 '--entity-type topics '
                                                 '--entity-name georgette '
                                                 '--add-config cleanup.policy=delete,'
                                                 'compression.type=gzip')

    def test_kafka_configs_del_config(self):
        set_module_args({
            'executable': None,
            'entity_type': 'topics',
            'entity_name': 'georgette',
            'configs': {'cleanup.policy': 'delete', 'compression.type': 'gzip'},
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Updated config for entity: topics 'georgette'"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_configs.main()
            self.assertTrue(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-configs --alter '
                                                 '--zookeeper carotte.localhost:2181 '
                                                 '--entity-type topics '
                                                 '--entity-name georgette '
                                                 '--delete-config cleanup.policy=delete,'
                                                 'compression.type=gzip')

    # Whether you have something to delete or not,
    # the kafka output is still the same: 'Updated config for [...]'
    def test_kafka_configs_del_config_no_change(self):
        set_module_args({
            'executable': None,
            'entity_type': 'topics',
            'entity_name': 'georgette',
            'configs': {'cleanup.policy': 'delete', 'compression.type': 'gzip'},
            'zookeeper': 'carotte.localhost:2181',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Updated config for entity: topics 'georgette'"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_configs.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with('/usr/bin/kafka-configs --alter '
                                                 '--zookeeper carotte.localhost:2181 '
                                                 '--entity-type topics '
                                                 '--entity-name georgette '
                                                 '--delete-config cleanup.policy=delete,'
                                                 'compression.type=gzip')

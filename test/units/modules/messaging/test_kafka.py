import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.modules.messaging import kafka_acls


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
    elif arg.endswith('kafka-acls'):
        return '/usr/bin/kafka-acls'
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

    def test_kafka_list(self):
        set_module_args({
            'executable': None,
            'topic': 'trololo',
            'authorizer_properties': 'zookeeper.connect=localhost',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Current ACLs for resource `Topic:trololo`: \\\\n \\\\t" + \
                "User:ANONYMOUS has Deny permission for operations: " + \
                "Describe from hosts: 127.0.0.2\\\\n\\\\t" + \
                "User:tintin has Allow permission for operations: " + \
                "Write from hosts: 127.0.0.1\\\\n\\\\tUser:tintin has " + \
                "Allow permission for operations: Read from hosts: " + \
                "127.0.0.1\\\\n\\\\tUser:bachibouzouk has Deny permission " + \
                "for operations: Describe from hosts: 127.0.0.2 \\\\n\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_acls.main()
            self.assertFalse(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with("/usr/bin/kafka-acls "
                                                 "--authorizer-properties 'zookeeper.connect=localhost' "
                                                 "--list "
                                                 "--topic 'trololo'")

    def test_kafka_acls_add(self):
        set_module_args({
            'executable': None,
            'action': 'add',
            'authorizer_properties': 'zookeeper.connect=localhost',
            'allow_host': ['127.0.0.1'],
            'allow_principal': ['User:lsp'],
            'operation': ['read', 'write'],
            'topic': 'trololo',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Adding ACLs for resource `Topic:trololo`: \\\\n \\\\t" + \
                "User:tintin has Allow permission for operations: " + \
                "Write from hosts: 127.0.0.1\\\\n\\\\tUser:tintin has " + \
                "Allow permission for operations: Read from hosts: " + \
                "127.0.0.1\\\\n\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_acls.main()
            self.assertTrue(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with("/usr/bin/kafka-acls "
                                                 "--authorizer-properties 'zookeeper.connect=localhost' "
                                                 "--add"
                                                 "--allow-host '127.0.0.1'"
                                                 "--allow-principal 'User:tintin'"
                                                 "--operation 'read,write'"
                                                 "--topic 'trololo'")

    def test_kafka_acls_delete(self):
        set_module_args({
            'executable': None,
            'action': 'remove',
            'authorizer_properties': 'zookeeper.connect=localhost',
            'operation': ['read'],
            'topic': 'trololo',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = "Adding ACLs for resource `Topic:trololo`: \\\\n \\\\t" + \
                "User:tintin has Allow permission for operations: " + \
                "Write from hosts: 127.0.0.1\\\\n\\\\tUser:tintin has " + \
                "Allow permission for operations: Read from hosts: " + \
                "127.0.0.1\\\\n\\\\n"
            stderr = ""
            mock_run_command.return_value = 0, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                kafka_acls.main()
            self.assertTrue(result.exception.args[0]['changed'])

        mock_run_command.assert_called_once_with("/usr/bin/kafka-acls "
                                                 "--authorizer-properties 'zookeeper.connect=localhost' "
                                                 "--force --remove"
                                                 "--operation 'read'"
                                                 "--topic 'trololo'")

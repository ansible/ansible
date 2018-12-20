
from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.modules.system.ufw as module

import json


# mock ufw messages

ufw_version_35 = """ufw 0.35\nCopyright 2008-2015 Canonical Ltd.\n"""
ufw_status_verbose_with_port_7000 = """Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
7000/tcp                   ALLOW IN    Anywhere
7000/tcp (v6)              ALLOW IN    Anywhere (v6)
"""

user_rules_with_port_7000 = """/etc/ufw/user.rules:### tuple ### allow any 7000 0.0.0.0/0 any 0.0.0.0/0 in
/etc/ufw/user6.rules:### tuple ### allow any 7000 ::/0 any ::/0 in
"""
skippg_adding_existing_rules = "Skipping adding existing rule\nSkipping adding existing rule (v6)\n"

delete_rules = ""

dry_mode_cmd = {
    "ufw status verbose": ufw_status_verbose_with_port_7000,
    "ufw --version": ufw_version_35,
    "grep '^### tuple' /lib/ufw/user.rules /lib/ufw/user6.rules /etc/ufw/user.rules /etc/ufw/user6.rules": user_rules_with_port_7000,
    "ufw --dry-run allow from any to any port 7000 proto tcp": skippg_adding_existing_rules,
    "ufw --dry-run delete allow from any to any port 7000 proto tcp | grep -E '^### tuple'": ""
}


def do_nothing_func(*args, **kwarg):
    return 0, dry_mode_cmd[args[0]], ""


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


def get_bin_path(self, arg, required=False):
    """Mock AnsibleModule.get_bin_path"""
    return arg


class TestUFW(unittest.TestCase):

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json,
                                                 get_bin_path=get_bin_path)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def test_check_mode_add_rules(self):
        set_module_args({
            'rule': 'allow',
            'proto': 'tcp',
            'port': '7000',
            '_ansible_check_mode': True
        })

        self.assertFalse(self.__getResult().exception.args[0]['changed'])

    def test_check_mode_delete_rules(self):

        set_module_args({
            'rule': 'allow',
            'proto': 'tcp',
            'port': '7000',
            'delete': 'yes',
            '_ansible_check_mode': True,
        })

        self.assertTrue(self.__getResult().exception.args[0]['changed'])

    def test_enable_mode(self):
        set_module_args({
            'state': 'enabled',
            '_ansible_check_mode': True
        })

        self.assertFalse(self.__getResult().exception.args[0]['changed'])

    def test_disable_mode(self):
        set_module_args({
            'state': 'disabled',
            '_ansible_check_mode': True
        })

        self.assertTrue(self.__getResult().exception.args[0]['changed'])

    def test_logging_off(self):
        set_module_args({
            'logging': 'off',
            '_ansible_check_mode': True
        })

        self.assertTrue(self.__getResult().exception.args[0]['changed'])

    def test_logging_on(self):
        set_module_args({
            'logging': 'on',
            '_ansible_check_mode': True
        })

        self.assertFalse(self.__getResult().exception.args[0]['changed'])

    def test_default_changed(self):
        set_module_args({
            'default': 'allow',
            "direction": "incoming",
            '_ansible_check_mode': True
        })
        self.assertTrue(self.__getResult().exception.args[0]['changed'])

    def test_default_not_changed(self):
        set_module_args({
            'default': 'deny',
            "direction": "incoming",
            '_ansible_check_mode': True
        })
        self.assertFalse(self.__getResult().exception.args[0]['changed'])

    def __getResult(self):
        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            mock_run_command.side_effect = do_nothing_func
            with self.assertRaises(AnsibleExitJson) as result:
                module.main()
        return result

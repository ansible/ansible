from ansible.compat.tests import unittest
from ansible.modules.system.pamd import PamdRule
from ansible.modules.system.pamd import PamdService
from ansible.modules.system.pamd import update_rule
from ansible.modules.system.pamd import insert_before_rule
from ansible.modules.system.pamd import insert_after_rule
from ansible.modules.system.pamd import remove_module_arguments
from ansible.modules.system.pamd import add_module_arguments
from ansible.modules.system.pamd import remove_rule

import re


class PamdRuleTestCase(unittest.TestCase):

    def test_simple(self):
        simple = "auth required pam_env.so".rstrip()
        module = PamdRule.rulefromstring(stringline=simple)
        module_string = re.sub(' +', ' ', str(module).replace('\t', ' '))
        self.assertEqual(simple, module_string.rstrip())
        self.assertEqual('', module.get_module_args_as_string())

    def test_simple_more(self):
        simple = "auth required pam_tally2.so deny=5 onerr=fail".rstrip()
        module = PamdRule.rulefromstring(stringline=simple)
        module_string = re.sub(' +', ' ', str(module).replace('\t', ' '))
        self.assertEqual(simple, module_string.rstrip())
        self.assertEqual('deny=5 onerr=fail',
                         module.get_module_args_as_string())

    def test_complicated_rule(self):
        complicated = "-auth [default=1 success=ok] pam_localuser.so".rstrip()
        module = PamdRule.rulefromstring(stringline=complicated)
        module_string = re.sub(' +', ' ', str(module).replace('\t', ' '))
        self.assertEqual(complicated, module_string.rstrip())
        self.assertEqual('', module.get_module_args_as_string())

    def test_more_complicated_rule(self):
        complicated = "auth"
        complicated += " [success=done ignore=ignore default=die]"
        complicated += " pam_unix.so"
        complicated += " try_first_pass".rstrip()
        module = PamdRule.rulefromstring(stringline=complicated)
        module_string = re.sub(' +', ' ', str(module).replace('\t', ' '))
        self.assertEqual(complicated, module_string.rstrip())
        self.assertEqual('try_first_pass', module.get_module_args_as_string())

    def test_rule_with_arg(self):
        line = "account       optional    pam_echo.so file=/etc/lockout.txt"
        module = PamdRule.rulefromstring(stringline=line)
        self.assertEqual(module.rule_type, 'account')
        self.assertEqual(module.rule_control, 'optional')
        self.assertEqual(module.rule_module_path, 'pam_echo.so')
        self.assertEqual(module.rule_module_args, ['file=/etc/lockout.txt'])

    def test_rule_with_args(self):
        line = "account       optional    pam_echo.so file1=/etc/lockout1.txt file2=/etc/lockout2.txt"
        module = PamdRule.rulefromstring(stringline=line)
        self.assertEqual(module.rule_type, 'account')
        self.assertEqual(module.rule_control, 'optional')
        self.assertEqual(module.rule_module_path, 'pam_echo.so')
        self.assertEqual(module.rule_module_args, ['file1=/etc/lockout1.txt', 'file2=/etc/lockout2.txt'])

    def test_less_than_in_args(self):
        rule = "auth requisite pam_succeed_if.so uid >= 1025 quiet_success"
        module = PamdRule.rulefromstring(stringline=rule)
        module_string = re.sub(' +', ' ', str(module).replace('\t', ' '))
        self.assertEqual(rule, module_string.rstrip())
        self.assertEqual('uid >= 1025 quiet_success', module.get_module_args_as_string())

    def test_trailing_comma(self):
        rule = "account required pam_access.so listsep=,"
        module = PamdRule.rulefromstring(stringline=rule)
        module_string = re.sub(' +', ' ', str(module).replace('\t', ' '))
        self.assertEqual(rule, module_string.rstrip())


class PamdServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.system_auth_string = """#%PAM-1.0
# This file is auto-generated.
# User changes will be destroyed the next time authconfig is run.
auth      \trequired\tpam_env.so
auth      \tsufficient\tpam_unix.so nullok try_first_pass
auth      \trequisite\tpam_succeed_if.so uid
auth      \trequired\tpam_deny.so

account   \trequired\tpam_unix.so
account   \tsufficient\tpam_localuser.so
account   \tsufficient\tpam_succeed_if.so uid
account   \trequired\tpam_permit.so
account   \trequired\tpam_access.so listsep=,
session   \tinclude\tsystem-auth

password  \trequisite\tpam_pwquality.so try_first_pass local_users_only retry=3 authtok_type=
password  \tsufficient\tpam_unix.so sha512 shadow nullok try_first_pass use_authtok
password  \trequired\tpam_deny.so

session   \toptional\tpam_keyinit.so revoke
session   \trequired\tpam_limits.so
-session  \toptional\tpam_systemd.so
session   \t[success=1 default=ignore]\tpam_succeed_if.so service in crond quiet use_uid
session   \t[success=1 test=me default=ignore]\tpam_succeed_if.so service in crond quiet use_uid
session   \trequired\tpam_unix.so"""

        self.pamd = PamdService()
        self.pamd.load_rules_from_string(self.system_auth_string)

    def test_load_rule_from_string(self):

        self.assertEqual(self.system_auth_string.rstrip().replace("\n\n", "\n"), str(self.pamd).rstrip().replace("\n\n", "\n"))

    def test_update_rule_type(self):
        old_rule = PamdRule.rulefromstring('auth      	required	pam_env.so')
        new_rule = PamdRule.rulefromstring('session      	required	pam_env.so')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_update_rule_control_simple(self):
        old_rule = PamdRule.rulefromstring('auth      	required	pam_env.so')
        new_rule = PamdRule.rulefromstring('auth      	sufficent	pam_env.so')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_update_rule_control_complex(self):
        old_rule = PamdRule.rulefromstring('session   	[success=1 default=ignore]	pam_succeed_if.so service in crond quiet use_uid')
        new_rule = PamdRule.rulefromstring('session   	[success=2 test=me default=ignore]	pam_succeed_if.so service in crond quiet use_uid')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_update_rule_control_more_complex(self):
        old_rule = PamdRule.rulefromstring('session   	[success=1 test=me default=ignore]	pam_succeed_if.so service in crond quiet use_uid')
        new_rule = PamdRule.rulefromstring('session   	[success=2 test=me default=ignore]	pam_succeed_if.so service in crond quiet use_uid')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_update_rule_module_path(self):
        old_rule = PamdRule.rulefromstring('auth      	required	pam_env.so')
        new_rule = PamdRule.rulefromstring('session      	required	pam_limits.so')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_update_rule_module_args(self):
        old_rule = PamdRule.rulefromstring('auth      	sufficient	pam_unix.so nullok try_first_pass')
        new_rule = PamdRule.rulefromstring('auth      	sufficient	pam_unix.so uid uid')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_update_first_three(self):
        old_rule = PamdRule.rulefromstring('auth      	required	pam_env.so')
        new_rule = PamdRule.rulefromstring('one      	two	three')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_update_first_three_with_module_args(self):
        old_rule = PamdRule.rulefromstring('auth      	sufficient	pam_unix.so nullok try_first_pass')
        new_rule = PamdRule.rulefromstring('one      	two	three')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_update_all_four(self):
        old_rule = PamdRule.rulefromstring('auth      	sufficient	pam_unix.so nullok try_first_pass')
        new_rule = PamdRule.rulefromstring('one      	two	three four five')
        update_rule(self.pamd, old_rule, new_rule)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_insert_before_rule(self):
        old_rule = PamdRule.rulefromstring('account   	required	pam_unix.so')
        new_rule = PamdRule.rulefromstring('account   	required	pam_permit.so')
        insert_before_rule(self.pamd, old_rule, new_rule)
        line_to_test = str(new_rule).rstrip()
        line_to_test += '\n'
        line_to_test += str(old_rule).rstrip()
        self.assertIn(line_to_test, str(self.pamd))

    def test_insert_after_rule(self):
        old_rule = PamdRule.rulefromstring('account   	required	pam_unix.so')
        new_rule = PamdRule.rulefromstring('account   	required	pam_permit.so arg1 arg2 arg3')
        insert_after_rule(self.pamd, old_rule, new_rule)
        line_to_test = str(old_rule).rstrip()
        line_to_test += '\n'
        line_to_test += str(new_rule).rstrip()
        self.assertIn(line_to_test, str(self.pamd))

    def test_insert_after_rule_last_rule(self):
        old_rule = PamdRule.rulefromstring('session   	required	pam_unix.so')
        new_rule = PamdRule.rulefromstring('session   	required	pam_permit.so arg1 arg2 arg3')
        insert_after_rule(self.pamd, old_rule, new_rule)
        line_to_test = str(old_rule).rstrip()
        line_to_test += '\n'
        line_to_test += str(new_rule).rstrip()
        self.assertIn(line_to_test, str(self.pamd))

    def test_remove_module_arguments_one(self):
        old_rule = PamdRule.rulefromstring('auth      	sufficient	pam_unix.so nullok try_first_pass')
        new_rule = PamdRule.rulefromstring('auth      	sufficient	pam_unix.so try_first_pass')
        args_to_remove = ['nullok']
        remove_module_arguments(self.pamd, old_rule, args_to_remove)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_remove_module_arguments_two(self):
        old_rule = PamdRule.rulefromstring('session   	[success=1 default=ignore]	pam_succeed_if.so service in crond quiet use_uid')
        new_rule = PamdRule.rulefromstring('session   	[success=1 default=ignore]	pam_succeed_if.so in quiet use_uid')
        args_to_remove = ['service', 'crond']
        remove_module_arguments(self.pamd, old_rule, args_to_remove)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_add_module_arguments_where_none_existed(self):
        old_rule = PamdRule.rulefromstring('account   	required	pam_unix.so')
        new_rule = PamdRule.rulefromstring('account   	required	pam_unix.so arg1 arg2= arg3=arg3')
        args_to_add = ['arg1', 'arg2=', 'arg3=arg3']
        add_module_arguments(self.pamd, old_rule, args_to_add)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))

    def test_add_module_arguments_where_some_existed(self):
        old_rule = PamdRule.rulefromstring('auth      	sufficient	pam_unix.so nullok try_first_pass')
        new_rule = PamdRule.rulefromstring('auth      	sufficient	pam_unix.so nullok try_first_pass arg1 arg2= arg3=arg3')
        args_to_add = ['arg1', 'arg2=', 'arg3=arg3']
        add_module_arguments(self.pamd, old_rule, args_to_add)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))

    def test_remove_rule(self):
        old_rule = PamdRule.rulefromstring('account   	required	pam_unix.so')
        remove_rule(self.pamd, old_rule)
        self.assertNotIn(str(old_rule).rstrip(), str(self.pamd))

    def test_add_module_args_with_string(self):
        old_rule = PamdRule.rulefromstring("account     required    pam_access.so")
        new_rule = PamdRule.rulefromstring("account     required    pam_access.so listsep=,")
        args_to_add = ['listsep=,']
        add_module_arguments(self.pamd, old_rule, args_to_add)
        self.assertIn(str(new_rule).rstrip(), str(self.pamd))

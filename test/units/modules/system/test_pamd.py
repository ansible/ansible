from __future__ import (absolute_import, division, print_function)
from ansible.compat.tests import unittest


from ansible.modules.system.pamd import PamdRule
from ansible.modules.system.pamd import PamdService


class PamdServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.system_auth_string = """#%PAM-1.0
# This file is auto-generated.
# User changes will be destroyed the next time authconfig is run.
@include   common-auth
@include   common-account
@include   common-session
auth       required pam_env.so
auth       sufficient pam_unix.so nullok try_first_pass
auth       requisite pam_succeed_if.so uid
auth       required pam_deny.so
# Test comment
auth       sufficient pam_rootok.so

account    required pam_unix.so
account    sufficient pam_localuser.so
account    sufficient pam_succeed_if.so uid
account		[success=1 default=ignore] \
    pam_succeed_if.so user = vagrant use_uid quiet
account    required pam_permit.so
account    required pam_access.so listsep=,
session    include system-auth

password   requisite pam_pwquality.so try_first_pass local_users_only retry=3 authtok_type=
password   sufficient pam_unix.so sha512 shadow nullok try_first_pass use_authtok
password   required pam_deny.so

session    optional pam_keyinit.so revoke
session    required pam_limits.so
-session   optional pam_systemd.so
session    [success=1 default=ignore] pam_succeed_if.so service in crond quiet use_uid
session    [success=1 test=me default=ignore] pam_succeed_if.so service in crond quiet use_uid
session    required pam_unix.so"""

        self.pamd = PamdService(self.system_auth_string)

    def test_properly_parsed(self):
        num_lines = len(self.system_auth_string.splitlines()) + 1
        num_lines_processed = len(str(self.pamd).splitlines())
        self.assertEqual(num_lines, num_lines_processed)

    def test_has_rule(self):
        self.assertTrue(self.pamd.has_rule('account', 'required', 'pam_permit.so'))
        self.assertTrue(self.pamd.has_rule('account', '[success=1 default=ignore]', 'pam_succeed_if.so'))

    def test_doesnt_have_rule(self):
        self.assertFalse(self.pamd.has_rule('account', 'requisite', 'pam_permit.so'))

    # Test Update
    def test_update_rule_type(self):
        self.assertTrue(self.pamd.update_rule('session', 'optional', 'pam_keyinit.so', new_type='account'))
        self.assertTrue(self.pamd.has_rule('account', 'optional', 'pam_keyinit.so'))
        test_rule = PamdRule('account', 'optional', 'pam_keyinit.so', 'revoke')
        self.assertIn(str(test_rule), str(self.pamd))

    def test_update_rule_that_doesnt_exist(self):
        self.assertFalse(self.pamd.update_rule('blah', 'blah', 'blah', new_type='account'))
        self.assertFalse(self.pamd.has_rule('blah', 'blah', 'blah'))
        test_rule = PamdRule('blah', 'blah', 'blah', 'account')
        self.assertNotIn(str(test_rule), str(self.pamd))

    def test_update_rule_type_two(self):
        self.assertTrue(self.pamd.update_rule('session', '[success=1 default=ignore]', 'pam_succeed_if.so', new_type='account'))
        self.assertTrue(self.pamd.has_rule('account', '[success=1 default=ignore]', 'pam_succeed_if.so'))
        test_rule = PamdRule('account', '[success=1 default=ignore]', 'pam_succeed_if.so')
        self.assertIn(str(test_rule), str(self.pamd))

    def test_update_rule_control_simple(self):
        self.assertTrue(self.pamd.update_rule('session', 'optional', 'pam_keyinit.so', new_control='required'))
        self.assertTrue(self.pamd.has_rule('session', 'required', 'pam_keyinit.so'))
        test_rule = PamdRule('session', 'required', 'pam_keyinit.so')
        self.assertIn(str(test_rule), str(self.pamd))

    def test_update_rule_control_complex(self):
        self.assertTrue(self.pamd.update_rule('session',
                                              '[success=1 default=ignore]',
                                              'pam_succeed_if.so',
                                              new_control='[success=2 test=me default=ignore]'))
        self.assertTrue(self.pamd.has_rule('session', '[success=2 test=me default=ignore]', 'pam_succeed_if.so'))
        test_rule = PamdRule('session', '[success=2 test=me default=ignore]', 'pam_succeed_if.so')
        self.assertIn(str(test_rule), str(self.pamd))

    def test_update_rule_control_more_complex(self):

        self.assertTrue(self.pamd.update_rule('session',
                                              '[success=1 test=me default=ignore]',
                                              'pam_succeed_if.so',
                                              new_control='[success=2 test=me default=ignore]'))
        self.assertTrue(self.pamd.has_rule('session', '[success=2 test=me default=ignore]', 'pam_succeed_if.so'))
        test_rule = PamdRule('session', '[success=2 test=me default=ignore]', 'pam_succeed_if.so')
        self.assertIn(str(test_rule), str(self.pamd))

    def test_update_rule_module_path(self):
        self.assertTrue(self.pamd.update_rule('auth', 'required', 'pam_env.so', new_path='pam_limits.so'))
        self.assertTrue(self.pamd.has_rule('auth', 'required', 'pam_limits.so'))

    def test_update_rule_module_path_slash(self):
        self.assertTrue(self.pamd.update_rule('auth', 'required', 'pam_env.so', new_path='/lib64/security/pam_duo.so'))
        self.assertTrue(self.pamd.has_rule('auth', 'required', '/lib64/security/pam_duo.so'))

    def test_update_rule_module_args(self):
        self.assertTrue(self.pamd.update_rule('auth', 'sufficient', 'pam_unix.so', new_args='uid uid'))
        test_rule = PamdRule('auth', 'sufficient', 'pam_unix.so', 'uid uid')
        self.assertIn(str(test_rule), str(self.pamd))

        test_rule = PamdRule('auth', 'sufficient', 'pam_unix.so', 'nullok try_first_pass')
        self.assertNotIn(str(test_rule), str(self.pamd))

    def test_update_first_three(self):
        self.assertTrue(self.pamd.update_rule('auth', 'required', 'pam_env.so',
                                              new_type='one', new_control='two', new_path='three'))
        self.assertTrue(self.pamd.has_rule('one', 'two', 'three'))

    def test_update_first_three_with_module_args(self):
        self.assertTrue(self.pamd.update_rule('auth', 'sufficient', 'pam_unix.so',
                                              new_type='one', new_control='two', new_path='three'))
        self.assertTrue(self.pamd.has_rule('one', 'two', 'three'))
        test_rule = PamdRule('one', 'two', 'three')
        self.assertIn(str(test_rule), str(self.pamd))
        self.assertIn(str(test_rule), str(self.pamd))

    def test_update_all_four(self):
        self.assertTrue(self.pamd.update_rule('auth', 'sufficient', 'pam_unix.so',
                                              new_type='one', new_control='two', new_path='three',
                                              new_args='four five'))
        test_rule = PamdRule('one', 'two', 'three', 'four five')
        self.assertIn(str(test_rule), str(self.pamd))

        test_rule = PamdRule('auth', 'sufficient', 'pam_unix.so', 'nullok try_first_pass')
        self.assertNotIn(str(test_rule), str(self.pamd))

    def test_update_rule_with_slash(self):
        self.assertTrue(self.pamd.update_rule('account', '[success=1 default=ignore]', 'pam_succeed_if.so',
                                              new_type='session', new_path='pam_access.so'))
        test_rule = PamdRule('session', '[success=1 default=ignore]', 'pam_access.so')
        self.assertIn(str(test_rule), str(self.pamd))

    # Insert Before

    def test_insert_before_rule(self):

        count = self.pamd.insert_before('account', 'required', 'pam_access.so',
                                        new_type='account', new_control='required', new_path='pam_limits.so')
        self.assertEqual(count, 1)

        rules = self.pamd.get("account", "required", "pam_access.so")
        for current_rule in rules:
            self.assertTrue(current_rule.prev.matches("account", "required", "pam_limits.so"))

    def test_insert_before_rule_where_rule_doesnt_exist(self):

        count = self.pamd.insert_before('account', 'sufficient', 'pam_access.so',
                                        new_type='account', new_control='required', new_path='pam_limits.so')
        self.assertFalse(count)

    def test_insert_before_rule_with_args(self):
        self.assertTrue(self.pamd.insert_before('account', 'required', 'pam_access.so',
                                                new_type='account', new_control='required', new_path='pam_limits.so',
                                                new_args='uid'))

        rules = self.pamd.get("account", "required", "pam_access.so")
        for current_rule in rules:
            self.assertTrue(current_rule.prev.matches("account", "required", "pam_limits.so", 'uid'))

    def test_insert_before_rule_test_duplicates(self):
        self.assertTrue(self.pamd.insert_before('account', 'required', 'pam_access.so',
                                                new_type='account', new_control='required', new_path='pam_limits.so'))

        self.pamd.insert_before('account', 'required', 'pam_access.so',
                                new_type='account', new_control='required', new_path='pam_limits.so')

        rules = self.pamd.get("account", "required", "pam_access.so")
        for current_rule in rules:
            previous_rule = current_rule.prev
            self.assertTrue(previous_rule.matches("account", "required", "pam_limits.so"))
            self.assertFalse(previous_rule.prev.matches("account", "required", "pam_limits.so"))

    def test_insert_before_first_rule(self):
        self.assertTrue(self.pamd.insert_before('auth', 'required', 'pam_env.so',
                                                new_type='account', new_control='required', new_path='pam_limits.so'))

    # Insert After
    def test_insert_after_rule(self):
        self.assertTrue(self.pamd.insert_after('account', 'required', 'pam_unix.so',
                                               new_type='account', new_control='required', new_path='pam_permit.so'))
        rules = self.pamd.get("account", "required", "pam_unix.so")
        for current_rule in rules:
            self.assertTrue(current_rule.next.matches("account", "required", "pam_permit.so"))

    def test_insert_after_rule_with_args(self):
        self.assertTrue(self.pamd.insert_after('account', 'required', 'pam_access.so',
                                               new_type='account', new_control='required', new_path='pam_permit.so',
                                               new_args='uid'))
        rules = self.pamd.get("account", "required", "pam_access.so")
        for current_rule in rules:
            self.assertTrue(current_rule.next.matches("account", "required", "pam_permit.so", "uid"))

    def test_insert_after_test_duplicates(self):
        self.assertTrue(self.pamd.insert_after('account', 'required', 'pam_access.so',
                                               new_type='account', new_control='required', new_path='pam_permit.so',
                                               new_args='uid'))
        self.assertFalse(self.pamd.insert_after('account', 'required', 'pam_access.so',
                                                new_type='account', new_control='required', new_path='pam_permit.so',
                                                new_args='uid'))

        rules = self.pamd.get("account", "required", "pam_access.so")
        for current_rule in rules:
            self.assertTrue(current_rule.next.matches("account", "required", "pam_permit.so", "uid"))
            self.assertFalse(current_rule.next.next.matches("account", "required", "pam_permit.so", "uid"))

    def test_insert_after_rule_last_rule(self):
        self.assertTrue(self.pamd.insert_after('session', 'required', 'pam_unix.so',
                                               new_type='account', new_control='required', new_path='pam_permit.so',
                                               new_args='uid'))
        rules = self.pamd.get("session", "required", "pam_unix.so")
        for current_rule in rules:
            self.assertTrue(current_rule.next.matches("account", "required", "pam_permit.so", "uid"))

    # Remove Module Arguments
    def test_remove_module_arguments_one(self):
        self.assertTrue(self.pamd.remove_module_arguments('auth', 'sufficient', 'pam_unix.so', 'nullok'))

    def test_remove_module_arguments_one_list(self):
        self.assertTrue(self.pamd.remove_module_arguments('auth', 'sufficient', 'pam_unix.so', ['nullok']))

    def test_remove_module_arguments_two(self):
        self.assertTrue(self.pamd.remove_module_arguments('session', '[success=1 default=ignore]', 'pam_succeed_if.so', 'service crond'))

    def test_remove_module_arguments_two_list(self):
        self.assertTrue(self.pamd.remove_module_arguments('session', '[success=1 default=ignore]', 'pam_succeed_if.so', ['service', 'crond']))

    def test_remove_module_arguments_where_none_existed(self):
        self.assertTrue(self.pamd.add_module_arguments('session', 'required', 'pam_limits.so', 'arg1 arg2= arg3=arg3'))

    def test_add_module_arguments_where_none_existed(self):
        self.assertTrue(self.pamd.add_module_arguments('account', 'required', 'pam_unix.so', 'arg1 arg2= arg3=arg3'))

    def test_add_module_arguments_where_none_existed_list(self):
        self.assertTrue(self.pamd.add_module_arguments('account', 'required', 'pam_unix.so', ['arg1', 'arg2=', 'arg3=arg3']))

    def test_add_module_arguments_where_some_existed(self):
        self.assertTrue(self.pamd.add_module_arguments('auth', 'sufficient', 'pam_unix.so', 'arg1 arg2= arg3=arg3'))

    def test_remove_rule(self):
        self.assertTrue(self.pamd.remove('account', 'required', 'pam_unix.so'))
        test_rule = PamdRule('account', 'required', 'pam_unix.so')
        self.assertNotIn(str(test_rule), str(self.pamd))

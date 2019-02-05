# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import

from ansible.modules.source_control.gitlab_user import GitLabUser

from .gitlab import (GitlabModuleTestCase,
                     python_version_match_requirement,
                     resp_find_user, resp_get_user, resp_get_user_keys,
                     resp_create_user_keys, resp_create_user, resp_delete_user,
                     resp_get_member, resp_get_group, resp_add_member,
                     resp_update_member, resp_get_member)

# Gitlab module requirements
if python_version_match_requirement():
    from gitlab.v4.objects import User

# Unit tests requirements
from httmock import with_httmock  # noqa


class TestGitlabUser(GitlabModuleTestCase):
    def setUp(self):
        super(TestGitlabUser, self).setUp()

        self.moduleUtil = GitLabUser(module=self.mock_module, gitlab_instance=self.gitlab_instance)

    @with_httmock(resp_find_user)
    def test_exist_user(self):
        rvalue = self.moduleUtil.existsUser("john_smith")

        self.assertEqual(rvalue, True)

        rvalue = self.moduleUtil.existsUser("paul_smith")

        self.assertEqual(rvalue, False)

    @with_httmock(resp_find_user)
    def test_find_user(self):
        user = self.moduleUtil.findUser("john_smith")

        self.assertEqual(type(user), User)
        self.assertEqual(user.name, "John Smith")
        self.assertEqual(user.id, 1)

    @with_httmock(resp_create_user)
    def test_create_user(self):
        user = self.moduleUtil.createUser({'email': 'john@example.com', 'password': 's3cur3s3cr3T',
                                           'username': 'john_smith', 'name': 'John Smith'})
        self.assertEqual(type(user), User)
        self.assertEqual(user.name, "John Smith")
        self.assertEqual(user.id, 1)

    @with_httmock(resp_get_user)
    def test_update_user(self):
        user = self.gitlab_instance.users.get(1)
        changed, newUser = self.moduleUtil.updateUser(user, {'name': "Jack Smith", "is_admin": "true"})

        self.assertEqual(changed, True)
        self.assertEqual(newUser.name, "Jack Smith")
        self.assertEqual(newUser.is_admin, "true")

        changed, newUser = self.moduleUtil.updateUser(user, {'name': "Jack Smith"})

        self.assertEqual(changed, False)

    @with_httmock(resp_find_user)
    @with_httmock(resp_delete_user)
    def test_delete_user(self):
        self.moduleUtil.existsUser("john_smith")
        rvalue = self.moduleUtil.deleteUser()

        self.assertEqual(rvalue, None)

    @with_httmock(resp_get_user)
    @with_httmock(resp_get_user_keys)
    def test_sshkey_exist(self):
        user = self.gitlab_instance.users.get(1)

        exist = self.moduleUtil.sshKeyExists(user, "Public key")
        self.assertEqual(exist, True)

        notExist = self.moduleUtil.sshKeyExists(user, "Private key")
        self.assertEqual(notExist, False)

    @with_httmock(resp_get_user)
    @with_httmock(resp_create_user_keys)
    @with_httmock(resp_get_user_keys)
    def test_create_sshkey(self):
        user = self.gitlab_instance.users.get(1)

        rvalue = self.moduleUtil.addSshKeyToUser(user, {
            'name': "Public key",
            'file': "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJe"
                    "jgt4596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4"
                    "soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0="})
        self.assertEqual(rvalue, False)

        rvalue = self.moduleUtil.addSshKeyToUser(user, {
            'name': "Private key",
            'file': "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDA1YotVDm2mAyk2tPt4E7AHm01sS6JZmcU"
                    "dRuSuA5zszUJzYPPUSRAX3BCgTqLqYx//UuVncK7YqLVSbbwjKR2Ez5lISgCnVfLVEXzwhv+"
                    "xawxKWmI7hJ5S0tOv6MJ+IxyTa4xcKwJTwB86z22n9fVOQeJTR2dSOH1WJrf0PvRk+KVNY2j"
                    "TiGHTi9AIjLnyD/jWRpOgtdfkLRc8EzAWrWlgNmH2WOKBw6za0az6XoG75obUdFVdW3qcD0x"
                    "c809OHLi7FDf+E7U4wiZJCFuUizMeXyuK/SkaE1aee4Qp5R4dxTR4TP9M1XAYkf+kF0W9srZ+mhF069XD/zhUPJsvwEF"})
        self.assertEqual(rvalue, True)

    @with_httmock(resp_get_group)
    @with_httmock(resp_get_member)
    def test_find_member(self):
        group = self.gitlab_instance.groups.get(1)

        user = self.moduleUtil.findMember(group, 1)
        self.assertEqual(user.username, "raymond_smith")

    @with_httmock(resp_get_user)
    @with_httmock(resp_get_group)
    @with_httmock(resp_get_group)
    @with_httmock(resp_get_member)
    @with_httmock(resp_add_member)
    @with_httmock(resp_update_member)
    def test_assign_user_to_group(self):
        group = self.gitlab_instance.groups.get(1)
        user = self.gitlab_instance.users.get(1)

        rvalue = self.moduleUtil.assignUserToGroup(user, group.id, "developer")
        self.assertEqual(rvalue, False)

        rvalue = self.moduleUtil.assignUserToGroup(user, group.id, "guest")
        self.assertEqual(rvalue, True)

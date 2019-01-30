# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from gitlab import Gitlab
from gitlab.v4.objects import User

from httmock import HTTMock  # noqa

from ansible.module_utils.basic import AnsibleModule
from ansible.modules.source_control.gitlab_user import GitLabUser

from units.utils.test_gitlab import (FakeAnsibleModule, resp_find_user, resp_get_user, resp_get_user_keys,
                                     resp_create_user_keys, resp_create_user, resp_delete_user,
                                     resp_get_member, resp_get_group, resp_add_member,
                                     resp_update_member)

try:
    import unittest
except ImportError:
    pass


class TestGitlabUser(unittest.TestCase):
    def setUp(self):
        self.gitlab_instance = Gitlab("http://localhost", private_token="private_token", api_version=4)
        self.moduleUtil = GitLabUser(module=FakeAnsibleModule(), gitlab_instance=self.gitlab_instance)

    def test_exist_user(self):
        with HTTMock(resp_find_user):
            rvalue = self.moduleUtil.existsUser("john_smith")

            self.assertEqual(rvalue, True)

            rvalue = self.moduleUtil.existsUser("paul_smith")

            self.assertEqual(rvalue, False)

    def test_find_user(self):
        with HTTMock(resp_find_user):
            user = self.moduleUtil.findUser("john_smith")
            self.assertEqual(type(user), User)
            self.assertEqual(user.name, "John Smith")
            self.assertEqual(user.id, 1)

    def test_create_user(self):
        with HTTMock(resp_create_user):
            user = self.moduleUtil.createUser({'email': 'john@example.com', 'password': 's3cur3s3cr3T',
                                               'username': 'john_smith', 'name': 'John Smith'})
            self.assertEqual(type(user), User)
            self.assertEqual(user.name, "John Smith")
            self.assertEqual(user.id, 1)

    def test_update_user(self):
        with HTTMock(resp_get_user):
            user = self.gitlab_instance.users.get(1)
            changed, newUser = self.moduleUtil.updateUser(user, {'name': "Jack Smith", "is_admin": "true"})

            self.assertEqual(changed, True)
            self.assertEqual(newUser.name, "Jack Smith")
            self.assertEqual(newUser.is_admin, "true")

            changed, newUser = self.moduleUtil.updateUser(user, {'name': "Jack Smith"})

            self.assertEqual(changed, False)

    def test_delete_user(self):
        with HTTMock(resp_find_user), HTTMock(resp_delete_user):
            self.moduleUtil.existsUser("john_smith")
            rvalue = self.moduleUtil.deleteUser()

            self.assertEqual(rvalue, None)

    def test_sshkey_exist(self):
        with HTTMock(resp_get_user), HTTMock(resp_get_user_keys):
            user = self.gitlab_instance.users.get(1)

            exist = self.moduleUtil.sshKeyExists(user, "Public key")
            self.assertEqual(exist, True)

            notExist = self.moduleUtil.sshKeyExists(user, "Private key")
            self.assertEqual(notExist, False)

    def test_create_sshkey(self):
        with HTTMock(resp_get_user), HTTMock(resp_create_user_keys), HTTMock(resp_get_user_keys):
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

    def test_find_member(self):
        with HTTMock(resp_get_group), HTTMock(resp_get_member):
            group = self.gitlab_instance.groups.get(1)

            user = self.moduleUtil.findMember(group, 1)
            self.assertEqual(user.username, "raymond_smith")

    def test_assign_user_to_group(self):
        with HTTMock(resp_get_user), HTTMock(resp_get_group), HTTMock(resp_get_member), HTTMock(resp_add_member), HTTMock(resp_update_member):
            group = self.gitlab_instance.groups.get(1)
            user = self.gitlab_instance.users.get(1)

            rvalue = self.moduleUtil.assignUserToGroup(user, group.id, "developer")
            self.assertEqual(rvalue, False)

            rvalue = self.moduleUtil.assignUserToGroup(user, group.id, "guest")
            self.assertEqual(rvalue, True)

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from gitlab import Gitlab
from gitlab.v4.objects import Group

from httmock import HTTMock  # noqa

from ansible.module_utils.basic import AnsibleModule
from ansible.modules.source_control.gitlab_group import GitLabGroup

from units.utils.test_gitlab import (FakeAnsibleModule, resp_get_group, resp_get_missing_group, resp_create_group,
                                     resp_create_subgroup, resp_delete_group, resp_find_group_project)

try:
    import unittest
except ImportError:
    pass


class TestGitlabGroup(unittest.TestCase):
    def setUp(self):
        self.gitlab_instance = Gitlab("http://localhost", private_token="private_token", api_version=4)
        self.moduleUtil = GitLabGroup(module=FakeAnsibleModule(), gitlab_instance=self.gitlab_instance)

    def test_exist_group(self):
        with HTTMock(resp_get_group):
            rvalue = self.moduleUtil.existsGroup(1)

            self.assertEqual(rvalue, True)

        with HTTMock(resp_get_missing_group):
            rvalue = self.moduleUtil.existsGroup(1)

            self.assertEqual(rvalue, False)

    def test_create_group(self):
        with HTTMock(resp_create_group):
            group = self.moduleUtil.createGroup({'name': "Foobar Group", 'path': "foo-bar"})
            self.assertEqual(type(group), Group)
            self.assertEqual(group.name, "Foobar Group")
            self.assertEqual(group.path, "foo-bar")
            self.assertEqual(group.id, 1)

    def test_create_subgroup(self):
        with HTTMock(resp_create_subgroup):
            group = self.moduleUtil.createGroup({'name': "BarFoo Group", 'path': "bar-foo", "parent_id": 1})
            self.assertEqual(type(group), Group)
            self.assertEqual(group.name, "BarFoo Group")
            self.assertEqual(group.full_path, "foo-bar/bar-foo")
            self.assertEqual(group.id, 2)
            self.assertEqual(group.parent_id, 1)

    def test_update_group(self):
        with HTTMock(resp_get_group):
            group = self.gitlab_instance.groups.get(1)
            changed, newGroup = self.moduleUtil.updateGroup(group, {'name': "BarFoo Group", "visibility": "private"})

            self.assertEqual(changed, True)
            self.assertEqual(newGroup.name, "BarFoo Group")
            self.assertEqual(newGroup.visibility, "private")

            changed, newGroup = self.moduleUtil.updateGroup(group, {'name': "BarFoo Group"})

            self.assertEqual(changed, False)

    def test_delete_group(self):
        with HTTMock(resp_get_group), HTTMock(resp_delete_group), HTTMock(resp_find_group_project):
            self.moduleUtil.existsGroup(1)

            rvalue = self.moduleUtil.deleteGroup()

            self.assertEqual(rvalue, None)

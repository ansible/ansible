# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import

from ansible.modules.source_control.gitlab_group import GitLabGroup

from .gitlab import (GitlabModuleTestCase,
                     python_version_match_requirement,
                     resp_get_group, resp_get_missing_group, resp_create_group,
                     resp_create_subgroup, resp_delete_group, resp_find_group_project)

# Gitlab module requirements
if python_version_match_requirement():
    from gitlab.v4.objects import Group

# Unit tests requirements
from httmock import with_httmock  # noqa


class TestGitlabGroup(GitlabModuleTestCase):
    def setUp(self):
        super(TestGitlabGroup, self).setUp()

        self.moduleUtil = GitLabGroup(module=self.mock_module, gitlab_instance=self.gitlab_instance)

    @with_httmock(resp_get_group)
    def test_exist_group(self):
        rvalue = self.moduleUtil.existsGroup(1)

        self.assertEqual(rvalue, True)

    @with_httmock(resp_get_missing_group)
    def test_exist_group(self):
        rvalue = self.moduleUtil.existsGroup(1)

        self.assertEqual(rvalue, False)

    @with_httmock(resp_create_group)
    def test_create_group(self):
        group = self.moduleUtil.createGroup({'name': "Foobar Group", 'path': "foo-bar"})

        self.assertEqual(type(group), Group)
        self.assertEqual(group.name, "Foobar Group")
        self.assertEqual(group.path, "foo-bar")
        self.assertEqual(group.id, 1)

    @with_httmock(resp_create_subgroup)
    def test_create_subgroup(self):
        group = self.moduleUtil.createGroup({'name': "BarFoo Group", 'path': "bar-foo", "parent_id": 1})

        self.assertEqual(type(group), Group)
        self.assertEqual(group.name, "BarFoo Group")
        self.assertEqual(group.full_path, "foo-bar/bar-foo")
        self.assertEqual(group.id, 2)
        self.assertEqual(group.parent_id, 1)

    @with_httmock(resp_get_group)
    def test_update_group(self):
        group = self.gitlab_instance.groups.get(1)
        changed, newGroup = self.moduleUtil.updateGroup(group, {'name': "BarFoo Group", "visibility": "private"})

        self.assertEqual(changed, True)
        self.assertEqual(newGroup.name, "BarFoo Group")
        self.assertEqual(newGroup.visibility, "private")

        changed, newGroup = self.moduleUtil.updateGroup(group, {'name': "BarFoo Group"})

        self.assertEqual(changed, False)

    @with_httmock(resp_get_group)
    @with_httmock(resp_find_group_project)
    @with_httmock(resp_delete_group)
    def test_delete_group(self):
        self.moduleUtil.existsGroup(1)

        print(self.moduleUtil.groupObject.projects)

        rvalue = self.moduleUtil.deleteGroup()

        self.assertEqual(rvalue, None)

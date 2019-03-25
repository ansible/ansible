# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import

from ansible.modules.source_control.gitlab_project import GitLabProject

from .gitlab import (GitlabModuleTestCase,
                     python_version_match_requirement,
                     resp_get_group, resp_get_project_by_name, resp_create_project,
                     resp_get_project, resp_delete_project, resp_get_user)

# Gitlab module requirements
if python_version_match_requirement():
    from gitlab.v4.objects import Project

# Unit tests requirements
from httmock import with_httmock  # noqa


class TestGitlabProject(GitlabModuleTestCase):
    @with_httmock(resp_get_user)
    def setUp(self):
        super(TestGitlabProject, self).setUp()

        self.gitlab_instance.user = self.gitlab_instance.users.get(1)
        self.moduleUtil = GitLabProject(module=self.mock_module, gitlab_instance=self.gitlab_instance)

    @with_httmock(resp_get_group)
    @with_httmock(resp_get_project_by_name)
    def test_project_exist(self):
        group = self.gitlab_instance.groups.get(1)

        rvalue = self.moduleUtil.existsProject(group, "diaspora-client")

        self.assertEqual(rvalue, True)

        rvalue = self.moduleUtil.existsProject(group, "missing-project")

        self.assertEqual(rvalue, False)

    @with_httmock(resp_get_group)
    @with_httmock(resp_create_project)
    def test_create_project(self):
        group = self.gitlab_instance.groups.get(1)
        project = self.moduleUtil.createProject(group, {"name": "Diaspora Client", "path": "diaspora-client", "namespace_id": group.id})

        self.assertEqual(type(project), Project)
        self.assertEqual(project.name, "Diaspora Client")

    @with_httmock(resp_get_project)
    def test_update_project(self):
        project = self.gitlab_instance.projects.get(1)

        changed, newProject = self.moduleUtil.updateProject(project, {"name": "New Name"})

        self.assertEqual(changed, True)
        self.assertEqual(type(newProject), Project)
        self.assertEqual(newProject.name, "New Name")

        changed, newProject = self.moduleUtil.updateProject(project, {"name": "New Name"})

        self.assertEqual(changed, False)
        self.assertEqual(newProject.name, "New Name")

    @with_httmock(resp_get_group)
    @with_httmock(resp_get_project_by_name)
    @with_httmock(resp_delete_project)
    def test_delete_project(self):
        group = self.gitlab_instance.groups.get(1)

        self.moduleUtil.existsProject(group, "diaspora-client")

        rvalue = self.moduleUtil.deleteProject()

        self.assertEqual(rvalue, None)

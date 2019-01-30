# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from gitlab import Gitlab
from gitlab.v4.objects import Project

from httmock import HTTMock  # noqa

from ansible.module_utils.basic import AnsibleModule
from ansible.modules.source_control.gitlab_project import GitLabProject

from units.utils.test_gitlab import (FakeAnsibleModule, resp_get_group, resp_get_project_by_name, resp_create_project,
                                     resp_get_project, resp_delete_project)

try:
    import unittest
except ImportError:
    pass


class TestGitlabRunner(unittest.TestCase):
    def setUp(self):
        self.gitlab_instance = Gitlab("http://localhost ", private_token="private_token", api_version=4)
        self.moduleUtil = GitLabProject(module=FakeAnsibleModule(), gitlab_instance=self.gitlab_instance)

    def test_project_exist(self):
        with HTTMock(resp_get_group), HTTMock(resp_get_project_by_name):
            group = self.gitlab_instance.groups.get(1)

            rvalue = self.moduleUtil.existsProject(group, "diaspora-client")

            self.assertEqual(rvalue, True)

            rvalue = self.moduleUtil.existsProject(group, "missing-project")

            self.assertEqual(rvalue, False)

    def test_create_project(self):
        with HTTMock(resp_get_group), HTTMock(resp_create_project):
            group = self.gitlab_instance.groups.get(1)
            project = self.moduleUtil.createProject(group, {"name": "Diaspora Client", "path": "diaspora-client", "namespace_id": group.id})

            self.assertEqual(type(project), Project)
            self.assertEqual(project.name, "Diaspora Client")

    def test_update_project(self):
        with HTTMock(resp_get_project):
            project = self.gitlab_instance.projects.get(1)

            changed, newProject = self.moduleUtil.updateProject(project, {"name": "New Name"})

            self.assertEqual(changed, True)
            self.assertEqual(type(newProject), Project)
            self.assertEqual(newProject.name, "New Name")

            changed, newProject = self.moduleUtil.updateProject(project, {"name": "New Name"})

            self.assertEqual(changed, False)
            self.assertEqual(newProject.name, "New Name")

    def test_delete_project(self):
        with HTTMock(resp_get_group), HTTMock(resp_get_project_by_name), HTTMock(resp_delete_project):
            group = self.gitlab_instance.groups.get(1)

            self.moduleUtil.existsProject(group, "diaspora-client")

            rvalue = self.moduleUtil.deleteProject()

            self.assertEqual(rvalue, None)

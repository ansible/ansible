# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.modules.source_control.gitlab_hooks import GitLabHook

from units.utils.test_gitlab import (FakeAnsibleModule, unitest_python_version_check_requirement,
                                     python_version_match_requirement,
                                     resp_get_project, resp_find_project_hook,
                                     resp_create_project_hook, resp_delete_project_hook)

# Gitlab module requirements
from gitlab import Gitlab

if python_version_match_requirement():
    from gitlab.v4.objects import ProjectHook

# Unit tests requirements
from httmock import with_httmock  # noqa

try:
    import unittest
except ImportError:
    pass


class TestGitlabHook(unittest.TestCase):
    def setUp(self):
        unitest_python_version_check_requirement(self)

        self.gitlab_instance = Gitlab("http://localhost", private_token="private_token", api_version=4)
        self.moduleUtil = GitLabHook(module=FakeAnsibleModule(), gitlab_instance=self.gitlab_instance)

    @with_httmock(resp_get_project)
    @with_httmock(resp_find_project_hook)
    def test_hook_exist(self):
        project = self.gitlab_instance.projects.get(1)

        rvalue = self.moduleUtil.existsHooks(project, "http://example.com/hook")

        self.assertEqual(rvalue, True)

        rvalue = self.moduleUtil.existsHooks(project, "http://gitlab.com/hook")

        self.assertEqual(rvalue, False)

    @with_httmock(resp_get_project)
    @with_httmock(resp_create_project_hook)
    def test_create_hook(self):
        project = self.gitlab_instance.projects.get(1)

        hook = self.moduleUtil.createHook(project, {"url": "http://example.com/hook"})

        self.assertEqual(type(hook), ProjectHook)
        self.assertEqual(hook.url, "http://example.com/hook")

    @with_httmock(resp_get_project)
    @with_httmock(resp_find_project_hook)
    def test_update_hook(self):
        project = self.gitlab_instance.projects.get(1)
        hook = self.moduleUtil.findHook(project, "http://example.com/hook")

        changed, newHook = self.moduleUtil.updateHook(hook, {"url": "http://gitlab.com/hook"})

        self.assertEqual(changed, True)
        self.assertEqual(type(newHook), ProjectHook)
        self.assertEqual(newHook.url, "http://gitlab.com/hook")

        changed, newHook = self.moduleUtil.updateHook(hook, {"url": "http://gitlab.com/hook"})

        self.assertEqual(changed, False)
        self.assertEqual(newHook.url, "http://gitlab.com/hook")

    @with_httmock(resp_get_project)
    @with_httmock(resp_find_project_hook)
    @with_httmock(resp_delete_project_hook)
    def test_delete_hook(self):
        project = self.gitlab_instance.projects.get(1)

        self.moduleUtil.existsHooks(project, "http://example.com/hook")

        rvalue = self.moduleUtil.deleteHook()

        self.assertEqual(rvalue, None)

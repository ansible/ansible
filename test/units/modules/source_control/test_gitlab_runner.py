# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from gitlab import Gitlab
from gitlab.v4.objects import Runner

from httmock import HTTMock  # noqa

from ansible.module_utils.basic import AnsibleModule
from ansible.modules.source_control.gitlab_runner import GitLabRunner

from units.utils.test_gitlab import (FakeAnsibleModule, resp_find_runners, resp_get_runner,
                                     resp_create_runner, resp_delete_runner)

try:
    import unittest
except ImportError:
    pass


class TestGitlabRunner(unittest.TestCase):
    def setUp(self):
        self.gitlab_instance = Gitlab("http://localhost", private_token="private_token", api_version=4)
        self.moduleUtil = GitLabRunner(module=FakeAnsibleModule(), gitlab_instance=self.gitlab_instance)

    def test_runner_exist(self):
        with HTTMock(resp_find_runners), HTTMock(resp_get_runner):
            rvalue = self.moduleUtil.existsRunner("test-1-20150125")

            self.assertEqual(rvalue, True)

            rvalue = self.moduleUtil.existsRunner("test-3-00000000")

            self.assertEqual(rvalue, False)

    def test_create_runner(self):
        with HTTMock(resp_create_runner):
            runner = self.moduleUtil.createRunner({"token": "token", "description": "test-1-20150125"})

            self.assertEqual(type(runner), Runner)
            self.assertEqual(runner.description, "test-1-20150125")

    def test_update_runner(self):
        with HTTMock(resp_find_runners), HTTMock(resp_get_runner):
            runner = self.moduleUtil.findRunner("test-1-20150125")

            changed, newRunner = self.moduleUtil.updateRunner(runner, {"description": "Runner description"})

            self.assertEqual(changed, True)
            self.assertEqual(type(newRunner), Runner)
            self.assertEqual(newRunner.description, "Runner description")

            changed, newRunner = self.moduleUtil.updateRunner(runner, {"description": "Runner description"})

            self.assertEqual(changed, False)
            self.assertEqual(newRunner.description, "Runner description")

    def test_delete_runner(self):
        with HTTMock(resp_find_runners), HTTMock(resp_get_runner), HTTMock(resp_delete_runner):
            self.moduleUtil.existsRunner("test-1-20150125")

            rvalue = self.moduleUtil.deleteRunner()

            self.assertEqual(rvalue, None)

# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import

import pytest

from ansible.modules.source_control.gitlab_deploy_key import GitLabDeployKey


def _dummy(x):
    """Dummy function.  Only used as a placeholder for toplevel definitions when the test is going
    to be skipped anyway"""
    return x


pytestmark = []
try:
    from .gitlab import (GitlabModuleTestCase,
                         python_version_match_requirement,
                         resp_get_project, resp_find_project_deploy_key,
                         resp_create_project_deploy_key, resp_delete_project_deploy_key)

    # GitLab module requirements
    if python_version_match_requirement():
        from gitlab.v4.objects import ProjectKey
except ImportError:
    pytestmark.append(pytest.mark.skip("Could not load gitlab module required for testing"))
    # Need to set these to something so that we don't fail when parsing
    GitlabModuleTestCase = object
    resp_get_project = _dummy
    resp_find_project_deploy_key = _dummy
    resp_create_project_deploy_key = _dummy
    resp_delete_project_deploy_key = _dummy

# Unit tests requirements
try:
    from httmock import with_httmock  # noqa
except ImportError:
    pytestmark.append(pytest.mark.skip("Could not load httmock module required for testing"))
    with_httmock = _dummy


class TestGitlabDeployKey(GitlabModuleTestCase):
    def setUp(self):
        super(TestGitlabDeployKey, self).setUp()

        self.moduleUtil = GitLabDeployKey(module=self.mock_module, gitlab_instance=self.gitlab_instance)

    @with_httmock(resp_get_project)
    @with_httmock(resp_find_project_deploy_key)
    def test_deploy_key_exist(self):
        project = self.gitlab_instance.projects.get(1)

        rvalue = self.moduleUtil.existsDeployKey(project, "Public key")

        self.assertEqual(rvalue, True)

        rvalue = self.moduleUtil.existsDeployKey(project, "Private key")

        self.assertEqual(rvalue, False)

    @with_httmock(resp_get_project)
    @with_httmock(resp_create_project_deploy_key)
    def test_create_deploy_key(self):
        project = self.gitlab_instance.projects.get(1)

        deploy_key = self.moduleUtil.createDeployKey(project, {"title": "Public key",
                                                               "key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM"
                                                               "4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxc"
                                                               "KDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4soW6NUlfD"
                                                               "zpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0="})

        self.assertEqual(type(deploy_key), ProjectKey)
        self.assertEqual(deploy_key.title, "Public key")

    @with_httmock(resp_get_project)
    @with_httmock(resp_find_project_deploy_key)
    @with_httmock(resp_create_project_deploy_key)
    def test_update_deploy_key(self):
        project = self.gitlab_instance.projects.get(1)
        deployKey = self.moduleUtil.findDeployKey(project, "Public key")

        changed, newDeploy_key = self.moduleUtil.updateDeployKey(deployKey, {"title": "Private key"})

        self.assertEqual(changed, True)
        self.assertEqual(type(newDeploy_key), ProjectKey)
        self.assertEqual(newDeploy_key.title, "Private key")

        changed, newDeploy_key = self.moduleUtil.updateDeployKey(deployKey, {"title": "Private key"})

        self.assertEqual(changed, False)
        self.assertEqual(newDeploy_key.title, "Private key")

    @with_httmock(resp_get_project)
    @with_httmock(resp_find_project_deploy_key)
    @with_httmock(resp_delete_project_deploy_key)
    def test_delete_deploy_key(self):
        project = self.gitlab_instance.projects.get(1)

        self.moduleUtil.existsDeployKey(project, "Public key")

        rvalue = self.moduleUtil.deleteDeployKey()

        self.assertEqual(rvalue, None)

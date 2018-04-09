# -*- coding: utf-8 -*-
# Copyright (c) 2018 Pierre-Louis Bonicoli <pierre-louis@libregerbil.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

from ansible.compat.tests.mock import MagicMock
from ansible.modules.source_control import gitlab_project

import pytest


@pytest.fixture
def patch_gitlab_project(mocker):
    mocker.patch.object(gitlab_project, 'HAS_GITLAB_PACKAGE', mocker.PropertyMock(return_value=True))


@pytest.mark.parametrize('patch_ansible_module', [{}], indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_without_required_parameters(capfd):
    """Failure must occurs when all parameters are missing"""

    with pytest.raises(SystemExit):
        gitlab_project.main()
    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'missing required arguments' in results['msg']


TEST_CASES = [
    [
        {
            'server_url': 'http://gitlab.test/gitlab',
            'validate_certs': True,
            'login_user': 'john',
            'login_token': 'TOKEN',
            'name': 'new_test_repo',
            'group': 'my_repo_group',
            'public': True,
            'visibility_level': 20,
            'issues_enabled': False,
            'wiki_enabled': True,
            'snippets_enabled': True,
            'import_url': 'http://gitlab.test/gitlab/gitrepothatdoesnotexist.git',
            'state': 'present'
        },
        {
            'msg': "Failed to create project 'new_test_repo'",
            'failed': True,
        }
    ],
]


@pytest.mark.parametrize('patch_ansible_module, testcase', TEST_CASES, indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_fail_if_url_import_doesnt_exist(mocker, capfd, patch_gitlab_project, testcase):
    """ Test for #36495

    Ensure errors are reported (meaning task report a failure),
    for example when url_import doesn't exist, an error must occur.
    """

    git = MagicMock()
    git.createprojectuser.return_value = False

    gitlab = MagicMock()
    gitlab.Gitlab.return_value = git
    gitlab_project.gitlab = gitlab

    with pytest.raises(SystemExit):
        gitlab_project.main()

    # Check that 1. createprojectuser method has been called 2. with expected parameter
    assert git.createprojectuser.call_count == 1
    assert git.createprojectuser.call_args[1]['import_url'] == 'http://gitlab.test/gitlab/gitrepothatdoesnotexist.git'

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results.get('failed') == testcase.get('failed')
    assert results['msg'] == testcase['msg']

from __future__ import annotations

import argparse
import json
import os
import typing as t

import pytest
import pytest_mock

if t.TYPE_CHECKING:
    from ansible_test._internal.ci.azp import AzurePipelinesChanges


def create_azure_pipelines_changes(mocker: pytest_mock.MockerFixture) -> AzurePipelinesChanges:
    """Prepare an AzurePipelinesChanges instance for testing."""
    from ansible_test._internal.ci.azp import AzurePipelinesChanges
    from ansible_test._internal.config import CommonConfig

    namespace = argparse.Namespace()
    namespace.color = False
    namespace.explain = False
    namespace.verbosity = False
    namespace.debug = False
    namespace.truncate = False
    namespace.redact = False
    namespace.display_traceback = False

    config = CommonConfig(namespace, 'sanity')

    env = dict(
        HOME=os.environ['HOME'],
        SYSTEM_COLLECTIONURI='https://dev.azure.com/ansible/',
        SYSTEM_TEAMPROJECT='ansible',
        BUILD_REPOSITORY_PROVIDER='GitHub',
        BUILD_SOURCEBRANCH='devel',
        BUILD_SOURCEBRANCHNAME='devel',
    )

    mocker.patch.dict(os.environ, env, clear=True)

    return AzurePipelinesChanges(config)


@pytest.mark.parametrize("status_code,response,expected_commits,expected_warning", (
    # valid 200 responses
    (200, dict(value=[]), None, None),
    (200, dict(value=[dict(sourceVersion='abc')]), {'abc'}, None),
    # invalid 200 responses
    (200, 'not-json', None, "Unable to find project due to HTTP 200 Non-JSON result."),
    (200, '"not-a-dict"', None, "Unexpected response format from HTTP 200 JSON result: string indices must be integers, not 'str'"),
    (200, dict(value='not-a-list'), None, "Unexpected response format from HTTP 200 JSON result: string indices must be integers, not 'str'"),
    (200, dict(value=['not-a-dict']), None, "Unexpected response format from HTTP 200 JSON result: string indices must be integers, not 'str'"),
    (200, dict(), None, "Missing 'value' key in response from HTTP 200 JSON result."),
    (200, dict(value=[{}]), None, "Missing 'sourceVersion' key in response from HTTP 200 JSON result."),
    # non-200 responses
    (404, '', None, "Unable to find project due to HTTP 404 Non-JSON result."),
    (404, '""', None, "Unable to find project due to HTTP 404 JSON result."),
    (404, dict(value=[]), None, "Unable to find project due to HTTP 404 JSON result."),
))
def test_get_successful_merge_run_commits(
    status_code: int,
    response: object,
    expected_commits: set[str] | None,
    expected_warning: str | None,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Verify AZP commit retrieval handles invalid responses gracefully."""
    from ansible_test._internal.ci.azp import AzurePipelinesChanges
    from ansible_test._internal.git import Git
    from ansible_test._internal.http import HttpClient, HttpResponse
    from ansible_test._internal.util import display

    if not isinstance(response, str):
        response = json.dumps(response)

    if expected_warning:
        expected_warning = f'Cannot determine changes. All tests will be executed. Reason: {expected_warning}'

    patched_get = mocker.patch.object(HttpClient, 'get', return_value=HttpResponse('GET', 'URL', status_code, response))
    patched_warning = mocker.patch.object(display, 'warning')

    mocker.patch.object(Git, 'run_git', return_value='')  # avoid git

    spy_get_successful_merge_run_commits = mocker.spy(AzurePipelinesChanges, 'get_successful_merge_run_commits')

    create_azure_pipelines_changes(mocker)

    assert patched_get.call_count == 1

    if expected_warning:
        patched_warning.assert_called_once_with(expected_warning)
    else:
        patched_warning.assert_not_called()

    assert spy_get_successful_merge_run_commits.spy_return == (expected_commits or set())

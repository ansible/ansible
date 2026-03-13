"""Support code for working with GitHub Actions."""

from __future__ import annotations

import os
import typing as t

from ..config import (
    CommonConfig,
    TestConfig,
)

from ..util import (
    ApplicationError,
    MissingEnvironmentVariable,
)

from . import (
    AuthContext,
    CIProvider,
    GeneratingAuthHelper,
)

CODE = 'gha'
JOB_ID_ENV_VAR = 'ANSIBLE_TEST_GHA_JOB_ID'
ARTIFACT_ID_ENV_VAR = 'ANSIBLE_TEST_GHA_SSH_KEY_ARTIFACT_ID'


class GitHubActions(CIProvider):
    """CI provider implementation for GitHub Actions."""

    def __init__(self) -> None:
        self.auth = GitHubActionsAuthHelper()

    @staticmethod
    def is_supported() -> bool:
        """Return True if this provider is supported in the current running environment."""
        return JOB_ID_ENV_VAR in os.environ and ARTIFACT_ID_ENV_VAR in os.environ

    @property
    def code(self) -> str:
        """Return a unique code representing this provider."""
        return CODE

    @property
    def name(self) -> str:
        """Return descriptive name for this provider."""
        return 'GitHub Actions'

    def generate_resource_prefix(self) -> str:
        """Return a resource prefix specific to this CI provider."""
        keys = [
            'GITHUB_REPOSITORY',
            JOB_ID_ENV_VAR,
        ]

        try:
            segments = [os.environ[key] for key in keys]
        except KeyError as ex:
            raise MissingEnvironmentVariable(name=ex.args[0]) from None

        prefix = '-'.join(['gha'] + segments)

        return prefix

    def get_base_commit(self, args: CommonConfig) -> str:
        """Return the base commit or an empty string."""
        return ''

    def detect_changes(self, args: TestConfig) -> t.Optional[list[str]]:
        """Initialize change detection."""
        return None

    def supports_core_ci_auth(self) -> bool:
        """Return True if Ansible Core CI is supported."""
        return True

    def prepare_core_ci_request(self, config: dict[str, object], context: AuthContext) -> dict[str, object]:
        try:
            owner, name = os.environ['GITHUB_REPOSITORY'].split('/', 1)

            request: dict[str, object] = dict(
                type="gha:ssh",
                config=config,
                repository_owner=owner,
                repository_name=name,
                job_id=int(os.environ[JOB_ID_ENV_VAR]),
                artifact_id=int(os.environ[ARTIFACT_ID_ENV_VAR]),
            )
        except KeyError as ex:
            raise MissingEnvironmentVariable(name=ex.args[0]) from None

        self.auth.sign_request(request, context)

        return request

    def get_git_details(self, args: CommonConfig) -> t.Optional[dict[str, t.Any]]:
        """Return details about git in the current environment."""
        return None


class GitHubActionsAuthHelper(GeneratingAuthHelper):
    """Authentication helper for GitHub Actions."""

    def generate_key_pair(self) -> None:
        raise ApplicationError(f'Missing SSH private key: {self.private_key_file}')

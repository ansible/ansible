from __future__ import annotations

import typing as t

import pytest

from pytest_mock import MockerFixture

from ansible._internal._errors._handler import ErrorHandler, ErrorAction
from ansible.parsing.vault import VaultSecretsContext, VaultSecret
from ansible._internal._templating._engine import _TemplateConfig
from units.mock.vault_helper import VaultTestHelper


# DTFIX-FUTURE: it'd be nice not to need to sync all controller-only fixtures here, but sunder values are excluded from `import *`,
#  and if we don't sunder the fixtures, they'll be unused args. Could also be handled with a managed import, module getattr, or others.
__all__ = ['_empty_vault_secrets_context', '_ignore_untrusted_template', '_vault_secrets_context', '_zap_vault_secrets_context']


@pytest.fixture
def _zap_vault_secrets_context() -> t.Generator[None]:
    """A fixture that disables any existing VaultSecretsContext both before and after the test."""
    # DTFIX-FUTURE: come up with a decent way to share this kind of fixture between controller contexts; we can't put it in top-level conftest since
    #  modules can't use it. Import from a shared controller fixture location, area-specific fixture support files, or ?
    VaultSecretsContext._current = None

    try:
        yield
    finally:
        VaultSecretsContext._current = None


@pytest.fixture
def _empty_vault_secrets_context(_zap_vault_secrets_context) -> t.Generator[None]:
    """A fixture that provides a `VaultSecretsContext` with no secrets."""
    VaultSecretsContext.initialize(VaultSecretsContext([]))

    yield


@pytest.fixture
def _vault_secrets_context(_zap_vault_secrets_context) -> t.Generator[VaultTestHelper]:
    """A fixture that initializes `VaultSecretsContext` with a single secret under the default ID and returns a `VaultTestHelper`."""
    secret = VaultSecret(b'secretbytesblah')

    VaultSecretsContext.initialize(VaultSecretsContext(secrets=[('default', secret)]))

    yield VaultTestHelper()


@pytest.fixture
def _ignore_untrusted_template(mocker: MockerFixture) -> t.Generator[None]:
    mocker.patch.object(_TemplateConfig, 'untrusted_template_handler', ErrorHandler(ErrorAction.IGNORE))

    yield

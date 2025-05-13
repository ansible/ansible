from __future__ import annotations

import json
import re

import pytest

from ansible._internal._json._legacy_encoder import LegacyControllerJSONEncoder
from ansible.parsing.vault import EncryptedString, VaultLib, VaultSecretsContext


@pytest.fixture
def data(request: pytest.FixtureRequest, _vault_secrets_context) -> object:
    if not isinstance(request.param, EncryptedString):
        return request.param

    secret = VaultSecretsContext.current().secrets[0][1]
    ciphertext = VaultLib().encrypt(request.param._ciphertext.encode(), secret).decode()
    return EncryptedString(ciphertext=ciphertext)


@pytest.mark.parametrize("data, kw, expected", (
    ("astring", {}, '"astring"'),
    ("astring", dict(preprocess_unsafe=True), '{"__ansible_unsafe": "astring"}'),
    (EncryptedString(ciphertext="encrypted"), dict(vault_to_text=True), '"encrypted"'),
    (EncryptedString(ciphertext="encrypted"), {}, '{"__ansible_vault": "$ANSIBLE_VAULT...'),
    (b'wasbytes', dict(_decode_bytes=True), '"wasbytes"'),
), indirect=['data'])
def test_legacy_encoder_conversions(data: object, kw: dict[str, object], expected: str, _vault_secrets_context) -> None:
    if expected.endswith('...'):
        expected_pattern = re.escape(expected[:-3])
    else:
        expected_pattern = re.escape(expected) + "$"

    assert re.match(expected_pattern, json.dumps(data, cls=LegacyControllerJSONEncoder, **kw))  # type:ignore[arg-type]

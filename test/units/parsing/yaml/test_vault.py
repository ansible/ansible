from __future__ import annotations

import json
import textwrap

import pytest

from ansible.errors import AnsibleJSONParserError
from ansible.parsing.vault import VaultHelper, EncryptedString
from ansible._internal._yaml._errors import AnsibleYAMLParserError
from ansible.parsing.utils.yaml import from_yaml

from ...mock.vault_helper import VaultTestHelper


def test_from_yaml_json_only(_vault_secrets_context: VaultTestHelper) -> None:
    """Ensure that from_yaml properly yields an `EncryptedString` instance for legacy-profile JSON with encoded vaulted values."""
    ciphertext = _vault_secrets_context.make_vault_ciphertext('mom')

    data = json.dumps(dict(hi=dict(
        __ansible_vault=ciphertext,
    )))

    result = from_yaml(data=data, file_name='/nope.json', json_only=True)

    assert isinstance(result['hi'], EncryptedString)
    assert result == dict(hi='mom')
    assert VaultHelper.get_ciphertext(result['hi'], with_tags=False) == ciphertext


def test_from_yaml(_vault_secrets_context: VaultTestHelper) -> None:
    ciphertext = _vault_secrets_context.make_vault_ciphertext('mom')

    data = f'hi: !vault |\n{textwrap.indent(ciphertext, "  ")}'

    result = from_yaml(data=data, file_name='/nope.yml')

    assert result == dict(hi='mom')
    assert VaultHelper.get_ciphertext(result['hi'], with_tags=False) == ciphertext


def test_from_yaml_invalid_json_vaulted_value() -> None:
    data = json.dumps(dict(hi=dict(__ansible_vault=1)))

    with pytest.raises(AnsibleJSONParserError, match="__ansible_vault is <class 'int'> not <class 'str'>"):
        from_yaml(data=data, json_only=True)


def test_from_yaml_invalid_yaml_vaulted_value() -> None:
    data = 'hi: !vault 1'

    with pytest.raises(AnsibleYAMLParserError, match="The '!vault' tag requires a string value."):
        from_yaml(data=data)


def test_from_yaml_does_not_recognize_json_vaulted_value() -> None:
    value = dict(hi=dict(__ansible_vault=dict(value_does_not_matter=True)))
    data = json.dumps(value)

    assert from_yaml(data=data) == value

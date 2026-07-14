from __future__ import annotations

import typing as t

import pytest

from ansible._internal._json import AnsibleVariableVisitor, EncryptedStringBehavior
from ansible.errors import AnsibleVariableTypeError
from ansible.parsing.vault import EncryptedString, AnsibleVaultError
from units.mock.vault_helper import VaultTestHelper


@pytest.mark.parametrize("behavior, decryptable, expected", (
    (EncryptedStringBehavior.PRESERVE, True, None),
    (EncryptedStringBehavior.PRESERVE, False, None),
    (EncryptedStringBehavior.DECRYPT, True, "plaintext"),
    (EncryptedStringBehavior.DECRYPT, False, AnsibleVaultError("no vault secrets")),
    (EncryptedStringBehavior.REDACT, True, "<redacted>"),
    (EncryptedStringBehavior.REDACT, False, "<redacted>"),
    (EncryptedStringBehavior.FAIL, True, AnsibleVariableTypeError("unsupported for variable storage")),
    (EncryptedStringBehavior.FAIL, False, AnsibleVariableTypeError("unsupported for variable storage")),
), ids=str)
def test_encrypted_string_behavior(
    behavior: EncryptedStringBehavior,
    decryptable: bool,
    expected: t.Any,
    _vault_secrets_context: None,
) -> None:
    if decryptable:
        value = VaultTestHelper.make_encrypted_string('plaintext')
    else:
        # valid ciphertext with intentionally unavailable secret
        value = EncryptedString(ciphertext=(
            '$ANSIBLE_VAULT;1.1;AES256\n'
            '333665623864636331356364306535613231613833616662656130613665336561316435393736366636663864396636326330626530643238653462333562350a396162623230643'
            '037396430383335386663363534353733386430643764303062633738613533336135653563313139373038333964316264633265376435370a326137363231646261303036356636'
            '37346430303361316436306130663461393832656134346639326365633830373361376236343961386164323538353962'
        ))

    avv = AnsibleVariableVisitor(encrypted_string_behavior=behavior)

    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            avv.visit(value)
    else:
        result = avv.visit(value)

        if expected is None:
            assert result is value
        else:
            assert result == expected

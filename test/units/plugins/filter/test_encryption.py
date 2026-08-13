from __future__ import annotations

import pytest

from ansible._internal._datatag._tags import VaultedValue
from ansible.plugins.filter.encryption import do_vault, do_unvault
from ansible.template import Templar, trust_as_template

PLAINTEXT = "data-to-encrypt"
SECRET = "vault-password"


def test_vault_wrap_object_tags_plaintext() -> None:
    result = do_vault(PLAINTEXT, SECRET, wrap_object=True)
    VaultedValue.get_required_tag(result)

    assert str(result) == PLAINTEXT


def test_vault_wrap_object_ciphertext_is_not_a_bytes_repr() -> None:
    """The tagged ciphertext must be a native string, not the repr of a bytes object."""
    result = do_vault(PLAINTEXT, SECRET, wrap_object=True)
    ciphertext = VaultedValue.get_required_tag(result).ciphertext

    assert ciphertext.startswith("$ANSIBLE_VAULT;")
    assert not ciphertext.startswith("b'")
    assert "\\n" not in ciphertext
    assert do_unvault(ciphertext, SECRET) == PLAINTEXT


@pytest.mark.parametrize("wrap_object", (True, False))
def test_vault_round_trip(wrap_object: bool) -> None:
    assert do_unvault(do_vault(PLAINTEXT, SECRET, wrap_object=wrap_object), SECRET) == PLAINTEXT


def _to_yaml(expression: str) -> str:
    templar = Templar(variables=dict(plaintext=PLAINTEXT, secret=SECRET))

    return templar.template(trust_as_template(expression))


def test_wrapped_vault_to_yaml_decrypt() -> None:
    result = _to_yaml("{{ plaintext | vault(secret, wrap_object=true) | to_yaml }}")

    assert result.strip() == PLAINTEXT
    assert SECRET not in result


def test_wrapped_vault_to_yaml_keep_encrypted() -> None:
    result = _to_yaml("{{ plaintext | vault(secret, wrap_object=true) | to_yaml(vault_behavior='keep_encrypted') }}")

    assert result.startswith("!vault |\n")
    assert "$ANSIBLE_VAULT;" in result
    assert "b'$ANSIBLE_VAULT" not in result
    assert "\\n" not in result

    ciphertext = "\n".join(line.strip() for line in result.splitlines()[1:] if line.strip())

    assert do_unvault(ciphertext, SECRET) == PLAINTEXT

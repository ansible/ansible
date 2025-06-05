from __future__ import annotations

import pytest

from ansible.errors import AnsibleUndefinedVariable
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.vault import EncryptedString
from ansible.template import Templar, trust_as_template, is_trusted_as_template
from units.mock.vault_helper import VaultTestHelper

undecryptable_value = EncryptedString(
    ciphertext="$ANSIBLE_VAULT;1.1;AES256\n"
               "35323961353038346165643738646465376139363061353835303739663538343266303232326635336535366264623635666532313563363065623"
               "8316530640a663362363763633436373439663031336634333830373964386564646364336538373763613136383663623330373239613163643633"
               "633835616438623261650a6361643765343766613931343266623263623231313739643139616233653833",
)


@pytest.mark.parametrize("filter_name", (
    "to_yaml",
    "to_nice_yaml",
))
def test_yaml_dump(filter_name: str, _vault_secrets_context: VaultTestHelper) -> None:
    """Verify YAML dumping round-trips only values which are expected to be supported."""
    payload = dict(
        trusted=trust_as_template('trusted'),
        untrusted="untrusted",
        decryptable=VaultTestHelper().make_encrypted_string("hi mom"),
        undecryptable=undecryptable_value,
    )

    original = dict(a_list=[payload])
    templar = Templar(variables=dict(original=original))
    result = templar.template(trust_as_template(f"{{{{ original | {filter_name} }}}}"))
    data = from_yaml(trust_as_template(result))

    assert len(data) == len(original)

    result_item = data['a_list'][0]
    original_item = original['a_list'][0]

    assert result_item['trusted'] == original_item['trusted']
    assert result_item['untrusted'] == original_item['untrusted']
    assert result_item['decryptable'] == original_item['decryptable']

    assert is_trusted_as_template(result_item['trusted'])
    assert is_trusted_as_template(result_item['untrusted'])  # round-tripping trust is NOT supported

    assert not is_trusted_as_template(result_item['decryptable'])

    assert result_item['decryptable']._ciphertext == original_item['decryptable']._ciphertext
    assert result_item['undecryptable']._ciphertext == original_item['undecryptable']._ciphertext

    assert not is_trusted_as_template(result_item['undecryptable'])


def test_yaml_dump_undefined() -> None:
    templar = Templar(variables=dict(dict_with_undefined=dict(undefined_value=trust_as_template("{{ bogus }}"))))

    with pytest.raises(AnsibleUndefinedVariable):
        templar.template(trust_as_template("{{ dict_with_undefined | to_yaml }}"))


@pytest.mark.parametrize("value, expected", (
    ((1, 2, 3), "[1, 2, 3]\n"),
    ({1, 2, 3}, "!!set {1: null, 2: null, 3: null}\n"),
    ("abc", "abc\n"),
    (b"abc", "!!binary |\n  YWJj\n"),
))
def test_yaml_dump_iterables(value: object, expected: object) -> None:
    result = Templar(variables=dict(value=value)).template(trust_as_template("{{ value | to_yaml }}"))

    assert result == expected

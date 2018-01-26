# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

import pytest

from ansible.plugins.filter import core as core_module
from ansible.plugins.filter.core import get_encrypted_password, HAS_PASSLIB
from units.mock.vault_helper import TextVaultSecret
from ansible.parsing import vault
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


def get_ave_unicode(plaintext):
    vault_password = "vault-password"
    vault_secret = TextVaultSecret(vault_password)
    vault_secrets = [('vault_secret', vault_secret), ('default', vault_secret)]

    return AnsibleVaultEncryptedUnicode.from_plaintext(
        plaintext, vault.VaultLib(vault_secrets), vault_secret)


# (password, hashtype, salt, expected_passlib, expected_no_passlib)
plaintext_testdata = [
    ('password', 'sha512', 'salt',
     '$6$rounds=656000$salt$h5bk4R2/x7KM0OsBeOpwdfYhpO4PEblXopKcO6vldXQzYXnhdxSfVBMnN4bmKjLt.QjWBNXxq.fqhfDs6mMOt1',
     '$6$salt$IxDD3jeSOb5eB1CX5LBsqZFVkJdido3OUILO5Ifz5iwMuTS4XMS130MTSuDDl3aCI6WouIL9AjRbLCelDCy.g.'
     ),
    ('password', 'md5', 'salt', '$1$salt$qJH7.N4xYta3aEG/dfqo/0',
     '$1$salt$qJH7.N4xYta3aEG/dfqo/0'),
]


@pytest.mark.skipif(not HAS_PASSLIB, reason="passlib not installed")
@pytest.mark.parametrize(
    "password,hashtype,salt,expected_passlib,expected_no_passlib",
    plaintext_testdata)
def test_hash_passlib(password, hashtype, salt, expected_passlib,
                      expected_no_passlib):
    computed_hash = get_encrypted_password(
        password, hashtype=hashtype, salt=salt)
    assert computed_hash == expected_passlib

    computed_hash_ave = get_encrypted_password(
        get_ave_unicode(password), hashtype=hashtype, salt=salt)
    assert computed_hash_ave == expected_passlib


@pytest.mark.skipif(
    sys.platform.startswith('darwin'),
    reason="passlib is required on Mac OS X/Darwin")
@pytest.mark.parametrize(
    "password,hashtype,salt,expected_passlib,expected_no_passlib",
    plaintext_testdata)
def test_hash_no_passlib(password, hashtype, salt, expected_passlib,
                         expected_no_passlib, monkeypatch):
    monkeypatch.setattr(core_module, 'HAS_PASSLIB', False)
    computed_hash = get_encrypted_password(
        password, hashtype=hashtype, salt=salt)
    assert computed_hash == expected_no_passlib

    computed_hash_ave = get_encrypted_password(
        get_ave_unicode(password), hashtype=hashtype, salt=salt)
    assert computed_hash_ave == expected_no_passlib

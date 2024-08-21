# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import codecs
import dataclasses
import time
import typing as t

import pytest
import pytest_mock

from ansible.parsing.vault import VaultSecret
from ansible.parsing.vault.methods import VaultSecretError, VaultMethodBase


@pytest.fixture
def patch_rot13_import(mocker: pytest_mock.MockerFixture) -> None:
    """Stuff a reference to this test module into runtime sys.modules to make it accessible to tests."""
    import sys

    from ansible.parsing.vault import methods
    from ansible import constants as C

    # insert rot13 encryption method
    patched_name = '.'.join((methods.__name__, __name__.rsplit('.', 1)[-1]))

    # patch/revert manually- patch.dict restores original state, fatally trashing stored module references loaded since patch
    sys.modules[patched_name] = sys.modules[__name__]

    # add rot13 as config option, to pass validation
    mocker.patch.dict(C.config._base_defs['VAULT_METHOD']['choices'], rot13='test vault method')

    try:
        yield
    finally:
        del sys.modules[patched_name]


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Params:
    kdf_sleep_sec: float = 0.25


class VaultMethod(VaultMethodBase):
    @staticmethod
    def _pretend_to_generate_key(params: Params) -> None:
        time.sleep(params.kdf_sleep_sec)

    @classmethod
    def encrypt(cls, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        params = Params(**options)

        cls._pretend_to_generate_key(params)

        ciphertext = codecs.encode(plaintext.decode(errors='surrogateescape'), 'rot13').encode(errors='surrogateescape')
        vaulttext = base64.b64encode(ciphertext).decode()

        return vaulttext

    @classmethod
    def decrypt(cls, vaulttext: str, secret: VaultSecret) -> bytes:
        if secret.bytes == b'not the correct secret':
            raise VaultSecretError()

        cls._pretend_to_generate_key(Params())

        ciphertext = base64.b64decode(vaulttext.encode())
        plaintext = codecs.decode(ciphertext.decode(errors='surrogateescape'), 'rot13').encode(errors='surrogateescape')

        return plaintext

# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import typing as t

from cryptography.hazmat.primitives.asymmetric import padding as P
from cryptography.hazmat.primitives import hashes as H
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key

from .. import VaultSecret
from . import VaultMethodBase, VaultSecretError


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class NoParams:
    """No options accepted. Any options provided will result in an error."""


class VaultMethod(VaultMethodBase):
    ''' Both public and private keys must RSA in PEM format and not protected by passhprase

    # generate RSA keys in pem format (only private), no passphrase
    ssh-keygen -m PEM -t rsa -b 4096  -f ~/.ssh/vault.pem

    # regen public since ssh-keygen still creates ssh format for it
    openssl rsa -pubout -in ~/.ssh/vault.pem > ~/.ssh/vault.pem.pub

    # encrypt file with public
    ansible-vault encrypt data.txt --vault-id ~/.ssh/vault.pem.pub -vvv --vault-method keyv1

    # decrypt file with private
    ansible-vault decrypt data.txt --vault-id ~/.ssh/vault.pem -vvv
    '''

    padding = P.OAEP(mgf=P.MGF1(algorithm=H.SHA256()), algorithm=H.SHA256(), label=None)

    @classmethod
    def encrypt(cls, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:

        NoParams(**options)

        public_key = load_pem_public_key(secret.bytes)
        encrypted_text = public_key.encrypt(plaintext, cls.padding)

        return base64.b64encode(encrypted_text)

    @classmethod
    def decrypt(cls, vaulttext: str, secret: VaultSecret) -> bytes:

        private_key = load_pem_private_key(secret.bytes, password=None)
        cipher_text = base64.b64decode(vaulttext)

        return private_key.decrypt(cipher_text, cls.padding)

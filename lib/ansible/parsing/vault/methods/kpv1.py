# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import dataclasses
import json
import typing as t

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key, load_ssh_public_key, load_ssh_private_key

from .. import VaultSecret
from . import VaultMethodBase, VaultSecretError


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class NoParams:
    """No options accepted. Any options provided will result in an error."""


class VaultMethod(VaultMethodBase):
    """ Both public and private keys must RSA in PEM or OpenSSH format and not protected by passhprase

    # generate RSA, private one in PEM format, use empty passphrase on prompt,
    # public key will be openssh format
    ssh-keygen -m PEM -t rsa -b 4096  -f ~/.ssh/vault.pem

    # optionally regen public key in PEM since ssh-keygen only creates it in ssh format
    openssl rsa -pubout -in ~/.ssh/vault.pem > ~/.ssh/vault.pem.pub

    # encrypt file with public
    ansible-vault encrypt data.txt --vault-id ~/.ssh/vault.pem.pub -vvv --vault-method keyv1

    # decrypt file with private
    ansible-vault decrypt data.txt --vault-id ~/.ssh/vault.pem -vvv
    """

    padding = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)

    @classmethod
    def encrypt(cls, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:

        NoParams(**options)

        b_key = secret.bytes
        try:
            public_key = load_ssh_public_key(b_key)
        except ValueError as e:
            try:
                public_key = load_pem_public_key(secret.bytes)
            except ValueError as e2:
                raise ValueError(f"Could not load vault secret public key, as ssh: {e!r}.\n Nor as pem: {e2!r}")

        if hasattr(public_key, 'encrypt'):
            encrypted_text = public_key.encrypt(plaintext, cls.padding)
        else:
            raise ValueError(f"Cannot use key of type '{type(public_key)}' to encrypt")

        return base64.b64encode(encrypted_text)

    @classmethod
    def decrypt(cls, vaulttext: str, secret: VaultSecret) -> bytes:

        b_key = secret.bytes
        try:
            private_key = load_pem_private_key(b_key, password=None)
        except ValueError as e:
            try:
                private_key = load_ssh_private_key(b_key, password=None)
            except ValueError as e2:
                raise ValueError(f"Could not load vault secret private key, as pem: {e!r}.\n Nor as ssh: {e2!r}")

        if hasattr(private_key, 'decrypt'):
            cipher_text = base64.b64decode(vaulttext)
        else:
            raise ValueError(f"Cannot use key of type '{type(public_key)}' to decrypt")

        return private_key.decrypt(cipher_text, cls.padding)

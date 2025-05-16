# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

# TODO: move to collection

DOCUMENTATION = """
    name: kpv1
    version_added: "2.4"
    short_description: Public/Private RSA ssh keys
    description:
        - Use public/private RSA ssh keys to encrypt/decrypt and base64 byte shield/armor
        - The vault secret must be the public key for encryption and the private for decryption
        - The private key cannot be passphrase protected when decrypting
    requirements:
        - cryptography (python)
"""

import base64
import dataclasses
import typing as t

try:
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key, load_ssh_public_key, load_ssh_private_key
    from cryptography.exceptions import UnsupportedAlgorithm
    CRYPT_ERROR = None
except Exception as e:
    # no import error as sometimes with FIPS weird exception types issued
    CRYPT_ERROR = e

from ansible.plugins.vault import VaultBase

if t.TYPE_CHECKING:
    from ansible.parsing.vault import VaultSecret


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class NoParams:
    """No options accepted. Any options provided will result in an error."""


class Vault(VaultBase):
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

    def __init__(self):

        if CRYPT_ERROR is not None:
            self._padding = None
            VaultBase._import_error('cryptography', CRYPT_ERROR)
        else:
            # Once lib supports more padding options, make this configurable via options
            self._padding = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)

    def encrypt(self, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:

        NoParams(**options)

        b_key = secret.bytes
        try:  # try to load as ssh key, if you fail, generic rsa key,
            public_key: t.Any = load_ssh_public_key(b_key)
        except (ValueError, UnsupportedAlgorithm)  as e:
            try:  # different class inheritance but both can have encrypt/decrypt
                public_key = load_pem_public_key(secret.bytes)
            except ValueError as e2:
                raise ValueError(f"Could not load vault secret public key, as ssh: {e!r}.\n Nor as pem: {e2!r}")
        except Exception as e:
                raise ValueError(f"Unexpected error while loading key for encryption") from e

        if hasattr(public_key, 'encrypt'):  # not all loadable keys are valid for encryption (yet?)
            try:
                encrypted_text = public_key.encrypt(plaintext, self._padding)
            except Exception as e:
                print(dir(public_key),'yop')
                raise e
        else:
            raise ValueError(f"Cannot use key of type '{type(public_key)}' to encrypt")

        return base64.b64encode(encrypted_text).decode()

    def decrypt(self, vaulttext: str, secret: VaultSecret) -> bytes:

        b_key = secret.bytes
        try:  # see encrypt comments
            private_key: t.Any = load_pem_private_key(b_key, password=None)
        except (ValueError, UnsupportedAlgorithm)  as e:
            try:
                private_key = load_ssh_private_key(b_key, password=None)
            except ValueError as e2:
                raise ValueError(f"Could not load vault secret private key, as pem: {e!r}.\n Nor as ssh: {e2!r}")
        except Exception as e:
                raise ValueError(f"Unexpected error while loading key for decryption") from e


        if hasattr(private_key, 'decrypt'):
            cipher_text = base64.b64decode(vaulttext)
        else:
            raise ValueError(f"Cannot use key of type '{type(private_key)}' to decrypt")

        return private_key.decrypt(cipher_text, self._padding)

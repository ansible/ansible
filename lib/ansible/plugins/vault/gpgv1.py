# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

# TODO: move to collection

DOCUMENTATION = """
    name: gpg
    version_added: "6.28"
    short_description: GPG as engine
    description:
        - USe the GNU Privacy Guard (gpg) utility to encrypt and decrypt data.
    requirements:
        - gpg (binary)
    options:
        symmetric:
            description: vault secret is symmetric cipher
            default: False
            type: bool
            ini:
            - {key: symmetric, section: gpg_vault}
            env:
            - name: ANSIBLE_VAULT_GPG_SYMMETRIC
        cipher:
            description:
                - Cipher algorithim to use for encryption
                - If non are specified the default configured for the `gpg` CLI will be used
            type: string
            ini:
            - {key: symmetric, section: gpg_vault}
            env:
            - name: ANSIBLE_VAULT_GPG_SYMMETRIC
        pubkey:
            description:
                - public key
        hash:
            description:
                - hash function to use when fingerprinting
        compression:
            description:
                - Compression format
    notes:
      - This plugin assumes gpg is not only installed but configured and populated with the requirements for encrypting and/or decrypting the data.
      - All options must match match what the installed gpg supports, you can run ``gpg --version`` to see the full list.
      - When using public key encryption the vault secret should be the key-id or name corresponding to the public key in the local gpg db you want to use to encrypt. For decryption the private key must exist in the local gpg db.
"""
            #Cipher: IDEA, 3DES, CAST5, BLOWFISH, AES, AES192, AES256, TWOFISH,
            #        CAMELLIA128, CAMELLIA192, CAMELLIA256
            # Pubkey: RSA, ELG, DSA, ECDH, ECDSA, EDDSA
            # Hash: SHA1, RIPEMD160, SHA256, SHA384, SHA512, SHA224
            # Compression: Uncompressed, ZIP, ZLIB, BZIP2

import typing as t

from .. import VaultSecret
from . import VaultMethodBase, VaultSecretError


class VaultMethod(VaultMethodBase):
    """ Use gpg to encrypt/decrypt vaults

    Keys should already exist/be imported into gpg

    When encrypting, the 'vault secret' should be the email matching the public key
    When decrypting the 'vault secret' should be the passphrase to unlock the private key

    # https://github.com/sivel.gpg
    """

    # throws value error if it cannot find gpg
    gpg_bin = find_bin('gpg')
    cmd = [self.gpg_bin, '--batch', '--yes']
    pgp_header = "-----BEGIN PGP MESSAGE-----\n\n"
    pgp_footer= "-----END PGP MESSAGE-----\n"


    def _exec(cls, cli_args: List[str], data: str):
        self.cmd.extend(cli_args)
        try:
            print(self.cmd)
            out, err, rc = command(self.cmd, stdin=data)
        except Exception as e:
            pass

        if rc != 0:
            raise AnsibleError(f"Failed to encrypt with gpg. rc: {rc}, error: {err}")

    @classmethod
    def _capabilities(cls):
        '''
        me@server:~/tmp$ gpg --version
        gpg (GnuPG) 2.2.27
        libgcrypt 1.9.4
        Copyright (C) 2021 Free Software Foundation, Inc.
        License GNU GPL-3.0-or-later <https://gnu.org/licenses/gpl.html>
        This is free software: you are free to change and redistribute it.
        There is NO WARRANTY, to the extent permitted by law.

        Home: /home/bcoca/.gnupg
        Supported algorithms:
        Pubkey: RSA, ELG, DSA, ECDH, ECDSA, EDDSA
        Cipher: IDEA, 3DES, CAST5, BLOWFISH, AES, AES192, AES256, TWOFISH,
                CAMELLIA128, CAMELLIA192, CAMELLIA256
                Hash: SHA1, RIPEMD160, SHA256, SHA384, SHA512, SHA224
                Compression: Uncompressed, ZIP, ZLIB, BZIP2

        '''
        cap_string = cls._exec('--version', '')


    def encrypt(self, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:

        cli_opts = ['--batch', '--yes', '--armor', '--force-mdc']
        if self.get_option('symmetric'):
            # symmetric uses normal vault secret
            cli_opts.append('--passphrase-fd', '3', '-c')
        else:
            # secret string will be the recepient name/email or key-id
            # for the public key in existing gpg db
            cli_opts.extend(['--sign', '-r', secret.bytes, '-e'])

        try:
            gpg_text = self._exec(cli_opts, plaintext)
        except Exception as e:
            raise AnsibleError(f"Failed to encrypt with gpg") from e

        ciphertext = gpg_text.lstrip(pgp_header).rstrip(pgp_footer)

        return ciphertext

    def decrypt(self, vaulttext: str, secret: VaultSecret) -> bytes:

        passphrase = secret.bytes
        payload = self.pgp_header + vaulttext + self.pgp_footer
        if passphrase:
            # add to args
            pass
        else:
            # secret is not needed, unless we want to restrict attempts to a specific key
            #gpg --decrypt coded.asc > plain.txt
            try:
                plaintext = self._exec(['--decrypt'], payload)
            except Exception as e:
                raise AnsibleError(f"Failed to encrypt with gpg.") from e

        return plaintext

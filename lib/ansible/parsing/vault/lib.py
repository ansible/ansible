# (c) 2014, James Tanner <tanner.jc@gmail.com>
# (c) 2016, Adrian Likins <alikins@redhat.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
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
from __future__ import division, absolute_import, print_function

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleVaultError, AnsibleVaultFormatError
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.utils.display import Display
from .ciphers import CIPHER_MAPPING, CIPHER_WRITE_WHITELIST, CIPHER_WHITELIST
from .util import parse_vaulttext_envelope, b_HEADER

display = Display()


class VaultLib:
    def __init__(self, secrets=None):
        self.secrets = secrets or []
        self.cipher_name = None
        self.b_version = b'1.2'

    @staticmethod
    def is_encrypted(vaulttext):
        return is_encrypted(vaulttext)

    def encrypt(self, plaintext, secret=None, vault_id=None, salt=None):
        """Vault encrypt a piece of data.

        :arg plaintext: a text or byte string to encrypt.
        :returns: a utf-8 encoded byte str of encrypted data.  The string
            contains a header identifying this as vault encrypted data and
            formatted to newline terminated lines of 80 characters.  This is
            suitable for dumping as is to a vault file.

        If the string passed in is a text string, it will be encoded to UTF-8
        before encryption.
        """

        if secret is None:
            if self.secrets:
                dummy, secret = match_encrypt_secret(self.secrets)
            else:
                raise AnsibleVaultError("A vault password must be specified to encrypt data")

        b_plaintext = to_bytes(plaintext, errors='surrogate_or_strict')

        if is_encrypted(b_plaintext):
            raise AnsibleError("input is already encrypted")

        if not self.cipher_name or self.cipher_name not in CIPHER_WRITE_WHITELIST:
            self.cipher_name = u"AES256"

        try:
            this_cipher = CIPHER_MAPPING[self.cipher_name]()
        except KeyError:
            raise AnsibleError(f"{self.cipher_name} cipher could not be found")

        # encrypt data
        if vault_id:
            display.vvvvv(f'Encrypting with vault_id "{to_text(vault_id)}" and vault secret {to_text(secret)}')
        else:
            display.vvvvv(f"Encrypting without a vault_id using vault secret {to_text(secret)}")

        b_ciphertext = this_cipher.encrypt(b_plaintext, secret, salt)

        # format the data for output to the file
        return format_vaulttext_envelope(b_ciphertext, self.cipher_name, vault_id=vault_id)

    def decrypt(self, vaulttext, filename=None, obj=None):
        '''Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :kwarg filename: a filename that the data came from.  This is only
            used to make better error messages in case the data cannot be
            decrypted.
        :returns: a byte string containing the decrypted data and the vault-id that was used

        '''
        plaintext, vault_id, vault_secret = self.decrypt_and_get_vault_id(vaulttext, filename=filename, obj=obj)
        return plaintext

    def decrypt_and_get_vault_id(self, vaulttext, filename=None, obj=None):
        """Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :kwarg filename: a filename that the data came from.  This is only
            used to make better error messages in case the data cannot be
            decrypted.
        :returns: a byte string containing the decrypted data and the vault-id vault-secret that was used

        """
        b_vaulttext = to_bytes(vaulttext, errors='strict', encoding='utf-8')

        if self.secrets is None:
            msg = "A vault password must be specified to decrypt data"
            if filename:
                msg += f" in file {to_native(filename)}"
            raise AnsibleVaultError(msg)

        if not is_encrypted(b_vaulttext):
            msg = "input is not vault encrypted data. "
            if filename:
                msg += f"{to_native(filename)} is not a vault encrypted file"
            raise AnsibleError(msg)

        b_vaulttext, dummy, cipher_name, vault_id = parse_vaulttext_envelope(b_vaulttext, filename=filename)

        # create the cipher object, note that the cipher used for decrypt can
        # be different than the cipher used for encrypt
        if cipher_name in CIPHER_WHITELIST:
            this_cipher = CIPHER_MAPPING[cipher_name]()
        else:
            raise AnsibleError(f"{cipher_name} cipher could not be found")

        b_plaintext = None

        if not self.secrets:
            raise AnsibleVaultError('Attempting to decrypt but no vault secrets found')

        # WARNING: Currently, the vault id is not required to match the vault id in the vault blob to
        #          decrypt a vault properly. The vault id in the vault blob is not part of the encrypted
        #          or signed vault payload. There is no cryptographic checking/verification/validation of the
        #          vault blobs vault id. It can be tampered with and changed. The vault id is just a nick
        #          name to use to pick the best secret and provide some ux/ui info.

        # iterate over all the applicable secrets (all of them by default) until one works...
        # if we specify a vault_id, only the corresponding vault secret is checked and
        # we check it first.

        vault_id_matchers = []
        vault_id_used = None
        vault_secret_used = None

        if vault_id:
            display.vvvvv(f'Found a vault_id ({to_text(vault_id)}) in the vaulttext')
            vault_id_matchers.append(vault_id)
            _matches = match_secrets(self.secrets, vault_id_matchers)
            if _matches:
                display.vvvvv(f'We have a secret associated with vault id ({to_text(vault_id)}), '
                              f'will try to use to decrypt {to_text(filename)}')
            else:
                display.vvvvv(f'Found a vault_id ({to_text(vault_id)}) '
                              'in the vault text, but we do not have a associated secret (--vault-id)')

        # Not adding the other secrets to vault_secret_ids enforces a match between the vault_id from the vault_text and
        # the known vault secrets.
        if not C.DEFAULT_VAULT_ID_MATCH:
            # Add all of the known vault_ids as candidates for decrypting a vault.
            vault_id_matchers.extend([_vault_id for _vault_id, _dummy in self.secrets if _vault_id != vault_id])

        matched_secrets = match_secrets(self.secrets, vault_id_matchers)

        # for vault_secret_id in vault_secret_ids:
        for vault_secret_id, vault_secret in matched_secrets:
            display.vvvvv(f"Trying to use vault secret=({to_text(vault_secret)}) "
                          f"id={to_text(vault_secret_id)} to decrypt {to_text(filename)}")

            try:
                # secret = self.secrets[vault_secret_id]
                display.vvvv(f"Trying secret {to_text(vault_secret)} for vault_id={to_text(vault_secret_id)}")
                b_plaintext = this_cipher.decrypt(b_vaulttext, vault_secret)
                if b_plaintext is not None:
                    vault_id_used = vault_secret_id
                    vault_secret_used = vault_secret
                    file_slug = ''
                    if filename:
                        file_slug = f' of "{filename}"'
                    display.vvvvv(f"Decrypt {to_text(file_slug)} successful with secret={to_text(vault_secret)} "
                                  f"and vault_id={to_text(vault_secret_id)}")
                    break
            except AnsibleVaultFormatError as exc:
                exc.obj = obj
                msg = "There was a vault format error"
                if filename:
                    msg += f' in {(to_text(filename))}'
                msg += f': {to_text(exc)}'
                display.warning(msg, formatted=True)
                raise
            except AnsibleError as e:
                display.vvvv(f'Tried to use the vault secret ({to_text(vault_secret_id)}) to decrypt '
                             f'({to_text(filename)}) but it failed. Error: {e}')
                continue
        else:
            msg = "Decryption failed (no vault secrets were found that could decrypt)"
            if filename:
                msg += f" on {to_native(filename)}"
            raise AnsibleVaultError(msg)

        if b_plaintext is None:
            msg = "Decryption failed"
            if filename:
                msg += f" on {to_native(filename)}"
            raise AnsibleError(msg)

        return b_plaintext, vault_id_used, vault_secret_used


def is_encrypted(data):
    """ Test if this is vault encrypted data blob

    :arg data: a byte or text string to test whether it is recognized as vault
        encrypted data
    :returns: True if it is recognized.  Otherwise, False.
    """
    try:
        # Make sure we have a byte string and that it only contains ascii
        # bytes.
        b_data = to_bytes(to_text(data, encoding='ascii', errors='strict', nonstring='strict'), encoding='ascii', errors='strict')
    except (UnicodeError, TypeError):
        # The vault format is pure ascii so if we failed to encode to bytes
        # via ascii we know that this is not vault data.
        # Similarly, if it's not a string, it's not vault data
        return False

    if b_data.startswith(b_HEADER):
        return True
    return False


def format_vaulttext_envelope(b_ciphertext, cipher_name, version=None, vault_id=None):
    """ Add header and format to 80 columns

        :arg b_ciphertext: the encrypted and hexlified data as a byte string
        :arg cipher_name: unicode cipher name (for ex, u'AES256')
        :arg version: unicode vault version (for ex, '1.2'). Optional ('1.1' is default)
        :arg vault_id: unicode vault identifier. If provided, the version will be bumped to 1.2.
        :returns: a byte str that should be dumped into a file.  It's
            formatted to 80 char columns and has the header prepended
    """

    if not cipher_name:
        raise AnsibleError("the cipher must be set before adding a header")

    version = version or '1.1'

    # If we specify a vault_id, use format version 1.2. For no vault_id, stick to 1.1
    if vault_id and vault_id != 'default':
        version = '1.2'

    b_version = to_bytes(version, 'utf-8', errors='strict')
    b_vault_id = to_bytes(vault_id, 'utf-8', errors='strict')
    b_cipher_name = to_bytes(cipher_name, 'utf-8', errors='strict')

    header_parts = [b_HEADER,
                    b_version,
                    b_cipher_name]

    if b_version == b'1.2' and b_vault_id:
        header_parts.append(b_vault_id)

    header = b';'.join(header_parts)

    b_vaulttext = [header]
    b_vaulttext += [b_ciphertext[i:i + 80] for i in range(0, len(b_ciphertext), 80)]
    b_vaulttext += [b'']
    b_vaulttext = b'\n'.join(b_vaulttext)

    return b_vaulttext


def match_secrets(secrets, target_vault_ids):
    '''Find all VaultSecret objects that are mapped to any of the target_vault_ids in secrets'''
    if not secrets:
        return []

    matches = [(vault_id, secret) for vault_id, secret in secrets if vault_id in target_vault_ids]
    return matches


def match_best_secret(secrets, target_vault_ids):
    '''Find the best secret from secrets that matches target_vault_ids

    Since secrets should be ordered so the early secrets are 'better' than later ones, this
    just finds all the matches, then returns the first secret'''
    matches = match_secrets(secrets, target_vault_ids)
    if matches:
        return matches[0]
    # raise exception?
    return None


def match_encrypt_vault_id_secret(secrets, encrypt_vault_id=None):
    # See if the --encrypt-vault-id matches a vault-id
    display.vvvv(f'encrypt_vault_id={to_text(encrypt_vault_id)}')

    if encrypt_vault_id is None:
        raise AnsibleError('match_encrypt_vault_id_secret requires a non None encrypt_vault_id')

    encrypt_vault_id_matchers = [encrypt_vault_id]
    encrypt_secret = match_best_secret(secrets, encrypt_vault_id_matchers)

    # return the best match for --encrypt-vault-id
    if encrypt_secret:
        return encrypt_secret

    # If we specified an encrypt_vault_id, and we couldn't find it, don't fall back to using the first/best secret
    raise AnsibleVaultError(f'Did not find a match for --encrypt-vault-id={encrypt_vault_id} '
                            f'in the known vault-ids {[_v for _v, _vs in secrets]}')


def match_encrypt_secret(secrets, encrypt_vault_id=None):
    """Find the best/first/only secret in secrets to use for encrypting"""

    display.vvvv(f'encrypt_vault_id={to_text(encrypt_vault_id)}')
    # See if the --encrypt-vault-id matches a vault-id
    if encrypt_vault_id:
        return match_encrypt_vault_id_secret(secrets, encrypt_vault_id=encrypt_vault_id)

    # Find the best/first secret from secrets since we didnt specify otherwise
    # ie, consider all of the available secrets as matches
    _vault_id_matchers = [_vault_id for _vault_id, dummy in secrets]
    best_secret = match_best_secret(secrets, _vault_id_matchers)

    # can be empty list sans any tuple
    return best_secret

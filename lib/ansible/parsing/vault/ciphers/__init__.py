# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from abc import abstractmethod


class VaultCipher:
    """
        Base class all ciphers must implement

        We don't mind duplication in the cipher classes, so limiting this to
        encrypt/decrypt as we want ciphers to be as self contained as possible
    """

    @classmethod
    @abstractmethod
    def encrypt(cls, b_plaintext, secret, salt=None, options=None):
        """
        :arg plaintext: A byte string to encrypt
        :arg secret: A populated VaultSecret object
        :arg salt: DEPRECATED Optional salt to use in encryption, for backwards compat
                  In most ciphers this will not be used
        :arg options: encryption options dict/data class

        :returns: A ciphered byte string that includes the encrypted data and
                  other needed items for decryption

        :raises: AnsibleVaultError do to missing requirements or other issues
        """
        pass

    @classmethod
    @abstractmethod
    def decrypt(cls, b_vaulttext, secret):
        """
        :arg b_vaulttext: A ciphered byte string that includes the encrypted
                data and other needed items for decryption
        :arg secret: A populated VaultSecret object

        :returns: decrypted byte string

        :raises: AnsibleVaultError do to missing requirements or other issues
        """
        pass

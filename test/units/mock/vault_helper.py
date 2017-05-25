
from nose.plugins.skip import SkipTest

from ansible import errors

from ansible.parsing.vault.ciphers import loader


def check_decrypt_prereqs(cipher_name):
    try:
        loader.get_decrypt_cipher(cipher_name)
    except errors.AnsibleVaultError as e:
        raise SkipTest(e)


def check_encrypt_prereqs(cipher_name):
    try:
        loader.get_encrypt_cipher(cipher_name)
    except errors.AnsibleVaultError as e:
        raise SkipTest(e)

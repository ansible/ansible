
from nose.plugins.skip import SkipTest

from ansible import errors

from ansible.parsing.vault import cipher_util


def check_decrypt_prereqs(cipher_name, cipher_mapping):
    try:
        cipher_util.get_decrypt_cipher(cipher_name, cipher_mapping)
    except errors.AnsibleVaultError as e:
        raise SkipTest(e)


def check_encrypt_prereqs(cipher_name, cipher_mapping):
    try:
        cipher_util.get_encrypt_cipher(cipher_name, cipher_mapping)
    except errors.AnsibleVaultError as e:
        raise SkipTest(e)

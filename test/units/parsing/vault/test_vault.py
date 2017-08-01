# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
#
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

import binascii
import io
import os
import tempfile

from binascii import hexlify
import pytest

from ansible.compat.tests import unittest

from ansible import errors
from ansible.module_utils import six
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing import vault

from units.mock.loader import DictDataLoader
from units.mock.vault_helper import TextVaultSecret


class TestVaultSecret(unittest.TestCase):
    def test(self):
        secret = vault.VaultSecret()
        secret.load()
        self.assertIsNone(secret._bytes)

    def test_bytes(self):
        some_text = u'私はガラスを食べられます。それは私を傷つけません。'
        _bytes = to_bytes(some_text)
        secret = vault.VaultSecret(_bytes)
        secret.load()
        self.assertEqual(secret.bytes, _bytes)


class TestPromptVaultSecret(unittest.TestCase):
    def test_empty_prompt_formats(self):
        secret = vault.PromptVaultSecret(vault_id='test_id', prompt_formats=[])
        secret.load()
        self.assertIsNone(secret._bytes)


class TestFileVaultSecret(unittest.TestCase):
    def test(self):
        secret = vault.FileVaultSecret()
        self.assertIsNone(secret._bytes)
        self.assertIsNone(secret._text)

    def test_repr_empty(self):
        secret = vault.FileVaultSecret()
        self.assertEqual(repr(secret), "FileVaultSecret()")

    def test_repr(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        fake_loader = DictDataLoader({tmp_file.name: 'sdfadf'})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=tmp_file.name)
        filename = tmp_file.name
        tmp_file.close()
        self.assertEqual(repr(secret), "FileVaultSecret(filename='%s')" % filename)

    def test_empty_bytes(self):
        secret = vault.FileVaultSecret()
        self.assertIsNone(secret.bytes)

    def test_file(self):
        password = 'some password'

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(to_bytes(password))
        tmp_file.close()

        fake_loader = DictDataLoader({tmp_file.name: 'sdfadf'})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=tmp_file.name)
        secret.load()

        os.unlink(tmp_file.name)

        self.assertEqual(secret.bytes, to_bytes(password))

    def test_file_not_a_directory(self):
        filename = '/dev/null/foobar'
        fake_loader = DictDataLoader({filename: 'sdfadf'})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=filename)
        self.assertRaisesRegexp(errors.AnsibleError,
                                '.*Could not read vault password file.*/dev/null/foobar.*Not a directory',
                                secret.load)

    def test_file_not_found(self):
        tmp_file = tempfile.NamedTemporaryFile()
        filename = tmp_file.name
        tmp_file.close()

        fake_loader = DictDataLoader({filename: 'sdfadf'})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=filename)
        self.assertRaisesRegexp(errors.AnsibleError,
                                '.*Could not read vault password file.*%s.*' % filename,
                                secret.load)


class TestScriptVaultSecret(unittest.TestCase):
    def test(self):
        secret = vault.ScriptVaultSecret()
        self.assertIsNone(secret._bytes)
        self.assertIsNone(secret._text)


class TestGetFileVaultSecret(unittest.TestCase):
    def test_file(self):
        password = 'some password'

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(to_bytes(password))
        tmp_file.close()

        fake_loader = DictDataLoader({tmp_file.name: 'sdfadf'})

        secret = vault.get_file_vault_secret(filename=tmp_file.name, loader=fake_loader)
        secret.load()

        os.unlink(tmp_file.name)

        self.assertEqual(secret.bytes, to_bytes(password))

    def test_file_not_a_directory(self):
        filename = '/dev/null/foobar'
        fake_loader = DictDataLoader({filename: 'sdfadf'})

        self.assertRaisesRegexp(errors.AnsibleError,
                                '.*The vault password file %s was not found.*' % filename,
                                vault.get_file_vault_secret,
                                filename=filename,
                                loader=fake_loader)

    def test_file_not_found(self):
        tmp_file = tempfile.NamedTemporaryFile()
        filename = tmp_file.name
        tmp_file.close()

        fake_loader = DictDataLoader({filename: 'sdfadf'})

        self.assertRaisesRegexp(errors.AnsibleError,
                                '.*The vault password file %s was not found.*' % filename,
                                vault.get_file_vault_secret,
                                filename=filename,
                                loader=fake_loader)


class TestVaultIsEncrypted(unittest.TestCase):
    def test_bytes_not_encrypted(self):
        b_data = b"foobar"
        self.assertFalse(vault.is_encrypted(b_data))

    def test_bytes_encrypted(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        self.assertTrue(vault.is_encrypted(b_data))

    def test_text_not_encrypted(self):
        b_data = to_text(b"foobar")
        self.assertFalse(vault.is_encrypted(b_data))

    def test_text_encrypted(self):
        b_data = to_text(b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible"))
        self.assertTrue(vault.is_encrypted(b_data))

    def test_invalid_text_not_ascii(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        self.assertFalse(vault.is_encrypted(data))

    def test_invalid_bytes_not_ascii(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        b_data = to_bytes(data, encoding='utf-8')
        self.assertFalse(vault.is_encrypted(b_data))


class TestVaultIsEncryptedFile(unittest.TestCase):
    def test_binary_file_handle_not_encrypted(self):
        b_data = b"foobar"
        b_data_fo = io.BytesIO(b_data)
        self.assertFalse(vault.is_encrypted_file(b_data_fo))

    def test_text_file_handle_not_encrypted(self):
        data = u"foobar"
        data_fo = io.StringIO(data)
        self.assertFalse(vault.is_encrypted_file(data_fo))

    def test_binary_file_handle_encrypted(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo))

    def test_text_file_handle_encrypted(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % to_text(hexlify(b"ansible"))
        data_fo = io.StringIO(data)
        self.assertTrue(vault.is_encrypted_file(data_fo))

    def test_binary_file_handle_invalid(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        b_data = to_bytes(data)
        b_data_fo = io.BytesIO(b_data)
        self.assertFalse(vault.is_encrypted_file(b_data_fo))

    def test_text_file_handle_invalid(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        data_fo = io.StringIO(data)
        self.assertFalse(vault.is_encrypted_file(data_fo))

    def test_file_already_read_from_finds_header(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible\ntesting\nfile pos")
        b_data_fo = io.BytesIO(b_data)
        b_data_fo.read(42)  # Arbitrary number
        self.assertTrue(vault.is_encrypted_file(b_data_fo))

    def test_file_already_read_from_saves_file_pos(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible\ntesting\nfile pos")
        b_data_fo = io.BytesIO(b_data)
        b_data_fo.read(69)  # Arbitrary number
        vault.is_encrypted_file(b_data_fo)
        self.assertEqual(b_data_fo.tell(), 69)

    def test_file_with_offset(self):
        b_data = b"JUNK$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible\ntesting\nfile pos")
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo, start_pos=4))

    def test_file_with_count(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible\ntesting\nfile pos")
        vault_length = len(b_data)
        b_data = b_data + u'ァ ア'.encode('utf-8')
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo, count=vault_length))

    def test_file_with_offset_and_count(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible\ntesting\nfile pos")
        vault_length = len(b_data)
        b_data = b'JUNK' + b_data + u'ァ ア'.encode('utf-8')
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo, start_pos=4, count=vault_length))


@pytest.mark.skipif(not vault.HAS_CRYPTOGRAPHY,
                    reason="Skipping cryptography tests because cryptography is not installed")
class TestVaultCipherAes256(unittest.TestCase):
    def setUp(self):
        self.vault_cipher = vault.VaultAES256()

    def test(self):
        self.assertIsInstance(self.vault_cipher, vault.VaultAES256)

    # TODO: tag these as slow tests
    def test_create_key_cryptography(self):
        b_password = b'hunter42'
        b_salt = os.urandom(32)
        b_key_cryptography = self.vault_cipher._create_key_cryptography(b_password, b_salt, key_length=32, iv_length=16)
        self.assertIsInstance(b_key_cryptography, six.binary_type)

    @pytest.mark.skipif(not vault.HAS_PYCRYPTO, reason='Not testing pycrypto key as pycrypto is not installed')
    def test_create_key_pycrypto(self):
        b_password = b'hunter42'
        b_salt = os.urandom(32)

        b_key_pycrypto = self.vault_cipher._create_key_pycrypto(b_password, b_salt, key_length=32, iv_length=16)
        self.assertIsInstance(b_key_pycrypto, six.binary_type)

    @pytest.mark.skipif(not vault.HAS_PYCRYPTO,
                        reason='Not comparing cryptography key to pycrypto key as pycrypto is not installed')
    def test_compare_new_keys(self):
        b_password = b'hunter42'
        b_salt = os.urandom(32)
        b_key_cryptography = self.vault_cipher._create_key_cryptography(b_password, b_salt, key_length=32, iv_length=16)

        b_key_pycrypto = self.vault_cipher._create_key_pycrypto(b_password, b_salt, key_length=32, iv_length=16)
        self.assertEqual(b_key_cryptography, b_key_pycrypto)

    def test_create_key_known_cryptography(self):
        b_password = b'hunter42'

        # A fixed salt
        b_salt = b'q' * 32  # q is the most random letter.
        b_key_1 = self.vault_cipher._create_key_cryptography(b_password, b_salt, key_length=32, iv_length=16)
        self.assertIsInstance(b_key_1, six.binary_type)

        # verify we get the same answer
        # we could potentially run a few iterations of this and time it to see if it's roughly constant time
        #  and or that it exceeds some minimal time, but that would likely cause unreliable fails, esp in CI
        b_key_2 = self.vault_cipher._create_key_cryptography(b_password, b_salt, key_length=32, iv_length=16)
        self.assertIsInstance(b_key_2, six.binary_type)
        self.assertEqual(b_key_1, b_key_2)

        # And again with pycrypto
        b_key_3 = self.vault_cipher._create_key_pycrypto(b_password, b_salt, key_length=32, iv_length=16)
        self.assertIsInstance(b_key_3, six.binary_type)

        # verify we get the same answer
        # we could potentially run a few iterations of this and time it to see if it's roughly constant time
        #  and or that it exceeds some minimal time, but that would likely cause unreliable fails, esp in CI
        b_key_4 = self.vault_cipher._create_key_pycrypto(b_password, b_salt, key_length=32, iv_length=16)
        self.assertIsInstance(b_key_4, six.binary_type)
        self.assertEqual(b_key_3, b_key_4)
        self.assertEqual(b_key_1, b_key_4)

    def test_create_key_known_pycrypto(self):
        b_password = b'hunter42'

        # A fixed salt
        b_salt = b'q' * 32  # q is the most random letter.
        b_key_3 = self.vault_cipher._create_key_pycrypto(b_password, b_salt, key_length=32, iv_length=16)
        self.assertIsInstance(b_key_3, six.binary_type)

        # verify we get the same answer
        # we could potentially run a few iterations of this and time it to see if it's roughly constant time
        #  and or that it exceeds some minimal time, but that would likely cause unreliable fails, esp in CI
        b_key_4 = self.vault_cipher._create_key_pycrypto(b_password, b_salt, key_length=32, iv_length=16)
        self.assertIsInstance(b_key_4, six.binary_type)
        self.assertEqual(b_key_3, b_key_4)

    def test_is_equal_is_equal(self):
        self.assertTrue(self.vault_cipher._is_equal(b'abcdefghijklmnopqrstuvwxyz', b'abcdefghijklmnopqrstuvwxyz'))

    def test_is_equal_unequal_length(self):
        self.assertFalse(self.vault_cipher._is_equal(b'abcdefghijklmnopqrstuvwxyz', b'abcdefghijklmnopqrstuvwx and sometimes y'))

    def test_is_equal_not_equal(self):
        self.assertFalse(self.vault_cipher._is_equal(b'abcdefghijklmnopqrstuvwxyz', b'AbcdefghijKlmnopQrstuvwxZ'))

    def test_is_equal_empty(self):
        self.assertTrue(self.vault_cipher._is_equal(b'', b''))

    def test_is_equal_non_ascii_equal(self):
        utf8_data = to_bytes(u'私はガラスを食べられます。それは私を傷つけません。')
        self.assertTrue(self.vault_cipher._is_equal(utf8_data, utf8_data))

    def test_is_equal_non_ascii_unequal(self):
        utf8_data = to_bytes(u'私はガラスを食べられます。それは私を傷つけません。')
        utf8_data2 = to_bytes(u'Pot să mănânc sticlă și ea nu mă rănește.')

        # Test for the len optimization path
        self.assertFalse(self.vault_cipher._is_equal(utf8_data, utf8_data2))
        # Test for the slower, char by char comparison path
        self.assertFalse(self.vault_cipher._is_equal(utf8_data, utf8_data[:-1] + b'P'))

    def test_is_equal_non_bytes(self):
        """ Anything not a byte string should raise a TypeError """
        self.assertRaises(TypeError, self.vault_cipher._is_equal, u"One fish", b"two fish")
        self.assertRaises(TypeError, self.vault_cipher._is_equal, b"One fish", u"two fish")
        self.assertRaises(TypeError, self.vault_cipher._is_equal, 1, b"red fish")
        self.assertRaises(TypeError, self.vault_cipher._is_equal, b"blue fish", 2)


@pytest.mark.skipif(not vault.HAS_PYCRYPTO,
                    reason="Skipping Pycrypto tests because pycrypto is not installed")
class TestVaultCipherAes256PyCrypto(TestVaultCipherAes256):
    def setUp(self):
        self.has_cryptography = vault.HAS_CRYPTOGRAPHY
        vault.HAS_CRYPTOGRAPHY = False
        super(TestVaultCipherAes256PyCrypto, self).setUp()

    def tearDown(self):
        vault.HAS_CRYPTOGRAPHY = self.has_cryptography
        super(TestVaultCipherAes256PyCrypto, self).tearDown()


class TestMatchSecrets(unittest.TestCase):
    def test_empty_tuple(self):
        secrets = [tuple()]
        vault_ids = ['vault_id_1']
        self.assertRaises(ValueError,
                          vault.match_secrets,
                          secrets, vault_ids)

    def test_empty_secrets(self):
        matches = vault.match_secrets([], ['vault_id_1'])
        self.assertEqual(matches, [])

    def test_single_match(self):
        secret = TextVaultSecret('password')
        matches = vault.match_secrets([('default', secret)], ['default'])
        self.assertEquals(matches, [('default', secret)])

    def test_no_matches(self):
        secret = TextVaultSecret('password')
        matches = vault.match_secrets([('default', secret)], ['not_default'])
        self.assertEquals(matches, [])

    def test_multiple_matches(self):
        secrets = [('vault_id1', TextVaultSecret('password1')),
                   ('vault_id2', TextVaultSecret('password2')),
                   ('vault_id1', TextVaultSecret('password3')),
                   ('vault_id4', TextVaultSecret('password4'))]
        vault_ids = ['vault_id1', 'vault_id4']
        matches = vault.match_secrets(secrets, vault_ids)

        self.assertEqual(len(matches), 3)
        expected = [('vault_id1', TextVaultSecret('password1')),
                    ('vault_id1', TextVaultSecret('password3')),
                    ('vault_id4', TextVaultSecret('password4'))]
        self.assertEqual([x for x, y in matches],
                         [a for a, b in expected])


@pytest.mark.skipif(not vault.HAS_CRYPTOGRAPHY,
                    reason="Skipping cryptography tests because cryptography is not installed")
class TestVaultLib(unittest.TestCase):
    def setUp(self):
        self.vault_password = "test-vault-password"
        text_secret = TextVaultSecret(self.vault_password)
        self.vault_secrets = [('default', text_secret),
                              ('test_id', text_secret)]
        self.v = vault.VaultLib(self.vault_secrets)

    def _vault_secrets(self, vault_id, secret):
        return [(vault_id, secret)]

    def _vault_secrets_from_password(self, vault_id, password):
        return [(vault_id, TextVaultSecret(password))]

    def test_encrypt(self):
        plaintext = u'Some text to encrypt in a café'
        b_vaulttext = self.v.encrypt(plaintext)

        self.assertIsInstance(b_vaulttext, six.binary_type)

        b_header = b'$ANSIBLE_VAULT;1.1;AES256\n'
        self.assertEqual(b_vaulttext[:len(b_header)], b_header)

    def test_encrypt_vault_id(self):
        plaintext = u'Some text to encrypt in a café'
        b_vaulttext = self.v.encrypt(plaintext, vault_id='test_id')

        self.assertIsInstance(b_vaulttext, six.binary_type)

        b_header = b'$ANSIBLE_VAULT;1.2;AES256;test_id\n'
        self.assertEqual(b_vaulttext[:len(b_header)], b_header)

    def test_encrypt_bytes(self):

        plaintext = to_bytes(u'Some text to encrypt in a café')
        b_vaulttext = self.v.encrypt(plaintext)

        self.assertIsInstance(b_vaulttext, six.binary_type)

        b_header = b'$ANSIBLE_VAULT;1.1;AES256\n'
        self.assertEqual(b_vaulttext[:len(b_header)], b_header)

    def test_encrypt_no_secret_empty_secrets(self):
        vault_secrets = []
        v = vault.VaultLib(vault_secrets)

        plaintext = u'Some text to encrypt in a café'
        self.assertRaisesRegexp(vault.AnsibleVaultError,
                                '.*A vault password must be specified to encrypt data.*',
                                v.encrypt,
                                plaintext)

    def test_is_encrypted(self):
        self.assertFalse(self.v.is_encrypted(b"foobar"), msg="encryption check on plaintext yielded false positive")
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        self.assertTrue(self.v.is_encrypted(b_data), msg="encryption check on headered text failed")

    def test_format_vaulttext_envelope(self):
        cipher_name = "TEST"
        b_ciphertext = b"ansible"
        b_vaulttext = vault.format_vaulttext_envelope(b_ciphertext,
                                                      cipher_name,
                                                      version=self.v.b_version,
                                                      vault_id='default')
        b_lines = b_vaulttext.split(b'\n')
        self.assertGreater(len(b_lines), 1, msg="failed to properly add header")

        b_header = b_lines[0]
        # self.assertTrue(b_header.endswith(b';TEST'), msg="header does not end with cipher name")

        b_header_parts = b_header.split(b';')
        self.assertEqual(len(b_header_parts), 4, msg="header has the wrong number of parts")
        self.assertEqual(b_header_parts[0], b'$ANSIBLE_VAULT', msg="header does not start with $ANSIBLE_VAULT")
        self.assertEqual(b_header_parts[1], self.v.b_version, msg="header version is incorrect")
        self.assertEqual(b_header_parts[2], b'TEST', msg="header does not end with cipher name")

        # And just to verify, lets parse the results and compare
        b_ciphertext2, b_version2, cipher_name2, vault_id2 = \
            vault.parse_vaulttext_envelope(b_vaulttext)
        self.assertEqual(b_ciphertext, b_ciphertext2)
        self.assertEqual(self.v.b_version, b_version2)
        self.assertEqual(cipher_name, cipher_name2)
        self.assertEqual('default', vault_id2)

    def test_parse_vaulttext_envelope(self):
        b_vaulttext = b"$ANSIBLE_VAULT;9.9;TEST\nansible"
        b_ciphertext, b_version, cipher_name, vault_id = vault.parse_vaulttext_envelope(b_vaulttext)
        b_lines = b_ciphertext.split(b'\n')
        self.assertEqual(b_lines[0], b"ansible", msg="Payload was not properly split from the header")
        self.assertEqual(cipher_name, u'TEST', msg="cipher name was not properly set")
        self.assertEqual(b_version, b"9.9", msg="version was not properly set")

    def test_parse_vaulttext_envelope_crlf(self):
        b_vaulttext = b"$ANSIBLE_VAULT;9.9;TEST\r\nansible"
        b_ciphertext, b_version, cipher_name, vault_id = vault.parse_vaulttext_envelope(b_vaulttext)
        b_lines = b_ciphertext.split(b'\n')
        self.assertEqual(b_lines[0], b"ansible", msg="Payload was not properly split from the header")
        self.assertEqual(cipher_name, u'TEST', msg="cipher name was not properly set")
        self.assertEqual(b_version, b"9.9", msg="version was not properly set")

    def test_encrypt_decrypt_aes(self):
        self.v.cipher_name = u'AES'
        vault_secrets = self._vault_secrets_from_password('default', 'ansible')
        self.v.secrets = vault_secrets
        # AES encryption code has been removed, so this is old output for
        # AES-encrypted 'foobar' with password 'ansible'.
        b_vaulttext = b'''$ANSIBLE_VAULT;1.1;AES
53616c7465645f5fc107ce1ef4d7b455e038a13b053225776458052f8f8f332d554809d3f150bfa3
fe3db930508b65e0ff5947e4386b79af8ab094017629590ef6ba486814cf70f8e4ab0ed0c7d2587e
786a5a15efeb787e1958cbdd480d076c
'''
        b_plaintext = self.v.decrypt(b_vaulttext)
        self.assertEqual(b_plaintext, b"foobar", msg="decryption failed")

    def test_encrypt_decrypt_aes256(self):
        self.v.cipher_name = u'AES256'
        plaintext = u"foobar"
        b_vaulttext = self.v.encrypt(plaintext)
        b_plaintext = self.v.decrypt(b_vaulttext)
        self.assertNotEqual(b_vaulttext, b"foobar", msg="encryption failed")
        self.assertEqual(b_plaintext, b"foobar", msg="decryption failed")

    def test_encrypt_decrypt_aes256_none_secrets(self):
        vault_secrets = self._vault_secrets_from_password('default', 'ansible')
        v = vault.VaultLib(vault_secrets)

        plaintext = u"foobar"
        b_vaulttext = v.encrypt(plaintext)

        # VaultLib will default to empty {} if secrets is None
        v_none = vault.VaultLib(None)
        # so set secrets None explicitly
        v_none.secrets = None
        self.assertRaisesRegexp(vault.AnsibleVaultError,
                                '.*A vault password must be specified to decrypt data.*',
                                v_none.decrypt,
                                b_vaulttext)

    def test_encrypt_decrypt_aes256_empty_secrets(self):
        vault_secrets = self._vault_secrets_from_password('default', 'ansible')
        v = vault.VaultLib(vault_secrets)

        plaintext = u"foobar"
        b_vaulttext = v.encrypt(plaintext)

        vault_secrets_empty = []
        v_none = vault.VaultLib(vault_secrets_empty)

        self.assertRaisesRegexp(vault.AnsibleVaultError,
                                '.*Attempting to decrypt but no vault secrets found.*',
                                v_none.decrypt,
                                b_vaulttext)

    def test_encrypt_decrypt_aes256_multiple_secrets_all_wrong(self):
        plaintext = u'Some text to encrypt in a café'
        b_vaulttext = self.v.encrypt(plaintext)

        vault_secrets = [('default', TextVaultSecret('another-wrong-password')),
                         ('wrong-password', TextVaultSecret('wrong-password'))]

        v_multi = vault.VaultLib(vault_secrets)
        self.assertRaisesRegexp(errors.AnsibleError,
                                '.*Decryption failed.*',
                                v_multi.decrypt,
                                b_vaulttext,
                                filename='/dev/null/fake/filename')

    def test_encrypt_decrypt_aes256_multiple_secrets_one_valid(self):
        plaintext = u'Some text to encrypt in a café'
        b_vaulttext = self.v.encrypt(plaintext)

        correct_secret = TextVaultSecret(self.vault_password)
        wrong_secret = TextVaultSecret('wrong-password')

        vault_secrets = [('default', wrong_secret),
                         ('corect_secret', correct_secret),
                         ('wrong_secret', wrong_secret)]

        v_multi = vault.VaultLib(vault_secrets)
        b_plaintext = v_multi.decrypt(b_vaulttext)
        self.assertNotEqual(b_vaulttext, to_bytes(plaintext), msg="encryption failed")
        self.assertEqual(b_plaintext, to_bytes(plaintext), msg="decryption failed")

    def test_encrypt_decrypt_aes256_existing_vault(self):
        self.v.cipher_name = u'AES256'
        b_orig_plaintext = b"Setec Astronomy"
        vaulttext = u'''$ANSIBLE_VAULT;1.1;AES256
33363965326261303234626463623963633531343539616138316433353830356566396130353436
3562643163366231316662386565383735653432386435610a306664636137376132643732393835
63383038383730306639353234326630666539346233376330303938323639306661313032396437
6233623062366136310a633866373936313238333730653739323461656662303864663666653563
3138'''

        b_plaintext = self.v.decrypt(vaulttext)
        self.assertEqual(b_plaintext, b_plaintext, msg="decryption failed")

        b_vaulttext = to_bytes(vaulttext, encoding='ascii', errors='strict')
        b_plaintext = self.v.decrypt(b_vaulttext)
        self.assertEqual(b_plaintext, b_orig_plaintext, msg="decryption failed")

    # FIXME This test isn't working quite yet.
    @pytest.mark.skip(reason='This test is not ready yet')
    def test_encrypt_decrypt_aes256_bad_hmac(self):

        self.v.cipher_name = 'AES256'
        # plaintext = "Setec Astronomy"
        enc_data = '''$ANSIBLE_VAULT;1.1;AES256
33363965326261303234626463623963633531343539616138316433353830356566396130353436
3562643163366231316662386565383735653432386435610a306664636137376132643732393835
63383038383730306639353234326630666539346233376330303938323639306661313032396437
6233623062366136310a633866373936313238333730653739323461656662303864663666653563
3138'''
        b_data = to_bytes(enc_data, errors='strict', encoding='utf-8')
        b_data = self.v._split_header(b_data)
        foo = binascii.unhexlify(b_data)
        lines = foo.splitlines()
        # line 0 is salt, line 1 is hmac, line 2+ is ciphertext
        b_salt = lines[0]
        b_hmac = lines[1]
        b_ciphertext_data = b'\n'.join(lines[2:])

        b_ciphertext = binascii.unhexlify(b_ciphertext_data)
        # b_orig_ciphertext = b_ciphertext[:]

        # now muck with the text
        # b_munged_ciphertext = b_ciphertext[:10] + b'\x00' + b_ciphertext[11:]
        # b_munged_ciphertext = b_ciphertext
        # assert b_orig_ciphertext != b_munged_ciphertext

        b_ciphertext_data = binascii.hexlify(b_ciphertext)
        b_payload = b'\n'.join([b_salt, b_hmac, b_ciphertext_data])
        # reformat
        b_invalid_ciphertext = self.v._format_output(b_payload)

        # assert we throw an error
        self.v.decrypt(b_invalid_ciphertext)

    def test_decrypt_non_default_1_2(self):
        b_expected_plaintext = to_bytes('foo bar\n')
        vaulttext = '''$ANSIBLE_VAULT;1.2;AES256;ansible_devel
65616435333934613466373335363332373764363365633035303466643439313864663837393234
3330656363343637313962633731333237313636633534630a386264363438363362326132363239
39363166646664346264383934393935653933316263333838386362633534326664646166663736
6462303664383765650a356637643633366663643566353036303162386237336233393065393164
6264'''

        vault_secrets = self._vault_secrets_from_password('default', 'ansible')
        v = vault.VaultLib(vault_secrets)

        b_vaulttext = to_bytes(vaulttext)

        b_plaintext = v.decrypt(b_vaulttext)
        self.assertEqual(b_expected_plaintext, b_plaintext)

        b_ciphertext, b_version, cipher_name, vault_id = vault.parse_vaulttext_envelope(b_vaulttext)
        self.assertEqual('ansible_devel', vault_id)
        self.assertEqual(b'1.2', b_version)

    def test_encrypt_encrypted(self):
        self.v.cipher_name = u'AES'
        b_vaulttext = b"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        vaulttext = to_text(b_vaulttext, errors='strict')
        self.assertRaises(errors.AnsibleError, self.v.encrypt, b_vaulttext)
        self.assertRaises(errors.AnsibleError, self.v.encrypt, vaulttext)

    def test_decrypt_decrypted(self):
        plaintext = u"ansible"
        self.assertRaises(errors.AnsibleError, self.v.decrypt, plaintext)

        b_plaintext = b"ansible"
        self.assertRaises(errors.AnsibleError, self.v.decrypt, b_plaintext)

    def test_cipher_not_set(self):
        plaintext = u"ansible"
        self.v.encrypt(plaintext)
        self.assertEquals(self.v.cipher_name, "AES256")


@pytest.mark.skipif(not vault.HAS_PYCRYPTO,
                    reason="Skipping Pycrypto tests because pycrypto is not installed")
class TestVaultLibPyCrypto(TestVaultLib):
    def setUp(self):
        self.has_cryptography = vault.HAS_CRYPTOGRAPHY
        vault.HAS_CRYPTOGRAPHY = False
        super(TestVaultLibPyCrypto, self).setUp()

    def tearDown(self):
        vault.HAS_CRYPTOGRAPHY = self.has_cryptography
        super(TestVaultLibPyCrypto, self).tearDown()

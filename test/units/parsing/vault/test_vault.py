# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import six

import binascii
import io
import os

from binascii import hexlify
from nose.plugins.skip import SkipTest

from ansible.compat.tests import unittest
from ansible.utils.unicode import to_bytes, to_unicode

from ansible import errors
from ansible.parsing.vault import VaultLib
from ansible.parsing import vault

# Counter import fails for 2.0.1, requires >= 2.6.1 from pip
try:
    from Crypto.Util import Counter
    HAS_COUNTER = True
except ImportError:
    HAS_COUNTER = False

# KDF import fails for 2.0.1, requires >= 2.6.1 from pip
try:
    from Crypto.Protocol.KDF import PBKDF2
    HAS_PBKDF2 = True
except ImportError:
    HAS_PBKDF2 = False

# AES IMPORTS
try:
    from Crypto.Cipher import AES as AES
    HAS_AES = True
except ImportError:
    HAS_AES = False


class TestVaultIsEncrypted(unittest.TestCase):
    def test_utf8_not_encrypted(self):
        b_data = "foobar".encode('utf8')
        self.assertFalse(vault.is_encrypted(b_data))

    def test_utf8_encrypted(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        b_data = data.encode('utf8')
        self.assertTrue(vault.is_encrypted(b_data))

    def test_bytes_not_encrypted(self):
        b_data = b"foobar"
        self.assertFalse(vault.is_encrypted(b_data))

    def test_bytes_encrypted(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" + hexlify(b"ansible")
        self.assertTrue(vault.is_encrypted(b_data))

    def test_unicode_not_encrypted_py3(self):
        if not six.PY3:
            raise SkipTest()
        data = u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        self.assertRaises(TypeError, vault.is_encrypted, data)

    def test_unicode_not_encrypted_py2(self):
        if six.PY3:
            raise SkipTest()
        data = u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        # py2 will take a unicode string, but that should always fails
        self.assertFalse(vault.is_encrypted(data))

    def test_unicode_is_encrypted_py3(self):
        if not six.PY3:
            raise SkipTest()
        data = "$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        # should still be a type error
        self.assertRaises(TypeError, vault.is_encrypted, data)

    def test_unicode_is_encrypted_py2(self):
        if six.PY3:
            raise SkipTest()
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        # THis works, but arguably shouldn't...
        self.assertTrue(vault.is_encrypted(data))


class TestVaultIsEncryptedFile(unittest.TestCase):
    def test_utf8_not_encrypted(self):
        b_data = "foobar".encode('utf8')
        b_data_fo = io.BytesIO(b_data)
        self.assertFalse(vault.is_encrypted_file(b_data_fo))

    def test_utf8_encrypted(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        b_data = data.encode('utf8')
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo))

    def test_bytes_not_encrypted(self):
        b_data = b"foobar"
        b_data_fo = io.BytesIO(b_data)
        self.assertFalse(vault.is_encrypted_file(b_data_fo))

    def test_bytes_encrypted(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" + hexlify(b"ansible")
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo))


class TestVaultCipherAes256(unittest.TestCase):
    def test(self):
        vault_cipher = vault.VaultAES256()
        self.assertIsInstance(vault_cipher, vault.VaultAES256)

    # TODO: tag these as slow tests
    def test_create_key(self):
        vault_cipher = vault.VaultAES256()
        password = 'hunter42'
        b_salt = os.urandom(32)
        b_key = vault_cipher.create_key(password=password, salt=b_salt, keylength=32, ivlength=16)
        self.assertIsInstance(b_key, six.binary_type)

    def test_create_key_known(self):
        vault_cipher = vault.VaultAES256()
        password = 'hunter42'

        # A fixed salt
        b_salt = b'q' * 32  # q is the most random letter.
        b_key = vault_cipher.create_key(password=password, salt=b_salt, keylength=32, ivlength=16)
        self.assertIsInstance(b_key, six.binary_type)

        # verify we get the same answer
        # we could potentially run a few iterations of this and time it to see if it's roughly constant time
        #  and or that it exceeds some minimal time, but that would likely cause unreliable fails, esp in CI
        b_key_2 = vault_cipher.create_key(password=password, salt=b_salt, keylength=32, ivlength=16)
        self.assertIsInstance(b_key, six.binary_type)
        self.assertEqual(b_key, b_key_2)

    def test_is_equal_is_equal(self):
        vault_cipher = vault.VaultAES256()
        res = vault_cipher.is_equal(b'abcdefghijklmnopqrstuvwxyz', b'abcdefghijklmnopqrstuvwxyz')
        self.assertTrue(res)

    def test_is_equal_unequal_length(self):
        vault_cipher = vault.VaultAES256()
        res = vault_cipher.is_equal(b'abcdefghijklmnopqrstuvwxyz', b'abcdefghijklmnopqrstuvwx and sometimes y')
        self.assertFalse(res)

    def test_is_equal_not_equal(self):
        vault_cipher = vault.VaultAES256()
        res = vault_cipher.is_equal(b'abcdefghijklmnopqrstuvwxyz', b'AbcdefghijKlmnopQrstuvwxZ')
        self.assertFalse(res)

    def test_is_equal_empty(self):
        vault_cipher = vault.VaultAES256()
        res = vault_cipher.is_equal(b'', b'')
        self.assertTrue(res)

    # NOTE: I'm not really sure what the method should do if it doesn't get bytes,
    #       but this at least sees if it explodes (maybe it should?)
    def test_is_equal_unicode_py3(self):
        if not six.PY3:
            raise SkipTest
        vault_cipher = vault.VaultAES256()
        self.assertRaises(TypeError, vault_cipher.is_equal,
                          u'私はガラスを食べられます。それは私を傷つけません。',
                          u'私はガラスを食べられます。それは私を傷つけません。')

    def test_is_equal_unicode_py2(self):
        if not six.PY2:
            raise SkipTest
        vault_cipher = vault.VaultAES256()
        res = vault_cipher.is_equal(u'私はガラスを食べられます。それは私を傷つけません。',
                                    u'私はガラスを食べられます。それは私を傷つけません。')
        self.assertTrue(res)

    def test_is_equal_unicode_different(self):
        vault_cipher = vault.VaultAES256()
        res = vault_cipher.is_equal(u'私はガラスを食べられます。それは私を傷つけません。',
                                    u'Pot să mănânc sticlă și ea nu mă rănește.')
        self.assertFalse(res)


class TestVaultLib(unittest.TestCase):

    def test_methods_exist(self):
        v = VaultLib('ansible')
        slots = ['is_encrypted',
                 'encrypt',
                 'decrypt',
                 '_format_output',
                 '_split_header',]
        for slot in slots:
            assert hasattr(v, slot), "VaultLib is missing the %s method" % slot

    def test_encrypt(self):
        v = VaultLib(password='the_unit_test_password')
        plaintext = u'Some text to encrypt.'
        ciphertext = v.encrypt(plaintext)

        self.assertIsInstance(ciphertext, (bytes, str))
        # TODO: assert something...

    def test_is_encrypted(self):
        v = VaultLib(None)
        assert not v.is_encrypted("foobar".encode('utf-8')), "encryption check on plaintext failed"
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        assert v.is_encrypted(data.encode('utf-8')), "encryption check on headered text failed"

    def test_is_encrypted_bytes(self):
        v = VaultLib(None)
        assert not v.is_encrypted(b"foobar"), "encryption check on plaintext failed"
        data = b"$ANSIBLE_VAULT;9.9;TEST\n%s" + hexlify(b"ansible")
        assert v.is_encrypted(data), "encryption check on headered text failed"

    def test_format_output(self):
        v = VaultLib('ansible')
        v.cipher_name = "TEST"
        sensitive_data = b"ansible"
        data = v._format_output(sensitive_data)
        lines = data.split(b'\n')
        assert len(lines) > 1, "failed to properly add header"
        header = to_bytes(lines[0])
        assert header.endswith(b';TEST'), "header does end with cipher name"
        header_parts = header.split(b';')
        assert len(header_parts) == 3, "header has the wrong number of parts"
        assert header_parts[0] == b'$ANSIBLE_VAULT', "header does not start with $ANSIBLE_VAULT"
        assert header_parts[1] == v.b_version, "header version is incorrect"
        assert header_parts[2] == b'TEST', "header does end with cipher name"

    def test_split_header(self):
        v = VaultLib('ansible')
        data = b"$ANSIBLE_VAULT;9.9;TEST\nansible"
        rdata = v._split_header(data)
        lines = rdata.split(b'\n')
        assert lines[0] == b"ansible"
        assert v.cipher_name == 'TEST', "cipher name was not set"
        assert v.b_version == b"9.9"

    def test_encrypt_decrypt_aes(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        v.cipher_name = u'AES'
        # AES encryption code has been removed, so this is old output for
        # AES-encrypted 'foobar' with password 'ansible'.
        enc_data = b'$ANSIBLE_VAULT;1.1;AES\n53616c7465645f5fc107ce1ef4d7b455e038a13b053225776458052f8f8f332d554809d3f150bfa3\nfe3db930508b65e0ff5947e4386b79af8ab094017629590ef6ba486814cf70f8e4ab0ed0c7d2587e\n786a5a15efeb787e1958cbdd480d076c\n'
        dec_data = v.decrypt(enc_data)
        assert dec_data == b"foobar", "decryption failed"

    def test_encrypt_decrypt_aes256(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        v.cipher_name = 'AES256'
        plaintext = "foobar"
        enc_data = v.encrypt(plaintext)
        dec_data = v.decrypt(enc_data)
        assert enc_data != b"foobar", "encryption failed"
        assert dec_data == b"foobar", "decryption failed"

    def test_encrypt_decrypt_aes256_existing_vault(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('test-vault-password')
        v.cipher_name = 'AES256'
        plaintext = b"Setec Astronomy"
        enc_data = '''$ANSIBLE_VAULT;1.1;AES256
33363965326261303234626463623963633531343539616138316433353830356566396130353436
3562643163366231316662386565383735653432386435610a306664636137376132643732393835
63383038383730306639353234326630666539346233376330303938323639306661313032396437
6233623062366136310a633866373936313238333730653739323461656662303864663666653563
3138'''

        dec_data = v.decrypt(enc_data)
        assert dec_data == plaintext, "decryption failed"

    def test_encrypt_decrypt_aes256_bad_hmac(self):
        # FIXME This test isn't working quite yet.
        raise SkipTest

        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('test-vault-password')
        v.cipher_name = 'AES256'
        # plaintext = "Setec Astronomy"
        enc_data = '''$ANSIBLE_VAULT;1.1;AES256
33363965326261303234626463623963633531343539616138316433353830356566396130353436
3562643163366231316662386565383735653432386435610a306664636137376132643732393835
63383038383730306639353234326630666539346233376330303938323639306661313032396437
6233623062366136310a633866373936313238333730653739323461656662303864663666653563
3138'''
        b_data = to_bytes(enc_data, errors='strict', encoding='utf-8')
        b_data = v._split_header(b_data)
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
        b_invalid_ciphertext = v._format_output(b_payload)

        # assert we throw an error
        v.decrypt(b_invalid_ciphertext)

    def test_encrypt_encrypted(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        v.cipher_name = 'AES'
        data = "$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(six.b("ansible"))
        self.assertRaises(errors.AnsibleError, v.encrypt, data,)

    def test_decrypt_decrypted(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        data = "ansible"
        self.assertRaises(errors.AnsibleError, v.decrypt, data)

    def test_cipher_not_set(self):
        # not setting the cipher should default to AES256
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        data = "ansible"
        v.encrypt(data)
        self.assertEquals(v.cipher_name, "AES256")

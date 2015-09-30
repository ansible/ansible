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

import getpass
import os
import shutil
import time
import tempfile
import six

from binascii import unhexlify
from binascii import hexlify
from nose.plugins.skip import SkipTest

from ansible.compat.tests import unittest
from ansible.utils.unicode import to_bytes, to_unicode

from ansible import errors
from ansible.parsing.vault import VaultLib

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

class TestVaultLib(unittest.TestCase):

    def test_methods_exist(self):
        v = VaultLib('ansible')
        slots = ['is_encrypted',
                 'encrypt',
                 'decrypt',
                 '_add_vault_header',
                 '_parse_vault_header',]
        for slot in slots:
            assert hasattr(v, slot), "VaultLib is missing the %s method" % slot

    def test_is_encrypted(self):
        v = VaultLib(None)
        assert not v.is_encrypted(u"foobar"), "encryption check on plaintext failed"
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(b"ansible")
        assert v.is_encrypted(data), "encryption check on headered text failed"

    def test_add_vault_header(self):
        v = VaultLib('ansible')
        sensitive_data = "ansible"
        data = v._add_vault_header(u'TEST', u'1.23', sensitive_data)
        lines = data.split(b'\n')
        assert len(lines) > 1, "failed to properly add header"
        header = to_unicode(lines[0])
        assert header.endswith(';TEST;1.23'), "header does end with cipher name"
        header_parts = header.split(';')
        assert len(header_parts) == 4, "header has the wrong number of parts"
        assert header_parts[0] == '$ANSIBLE_VAULT', "header does not start with $ANSIBLE_VAULT"
        assert header_parts[1] == b'1.2', "header version is incorrect"
        assert header_parts[2] == 'TEST', "cipher name is incorrect"
        assert header_parts[3] == b'1.23', "cipher version is incorrect"

    def test_parse_vault_header(self):
        v = VaultLib('ansible')
        data = b"$ANSIBLE_VAULT;0.9;TEST\nansible"
        (vault_version, cipher_name, cipher_version, rdata) = v._parse_vault_header(data)
        lines = rdata.split(b'\n')
        self.assertEqual(lines[0], b"ansible")
        self.assertEqual(cipher_name, b'TEST', msg="cipher name was not set")
        self.assertEqual(vault_version, b"0.9")
        self.assertEqual(cipher_version, vault_version)

        data = b"$ANSIBLE_VAULT;1.1;TEST\nansible"
        (vault_version, cipher_name, cipher_version, rdata) = v._parse_vault_header(data)
        lines = rdata.split(b'\n')
        self.assertEqual(lines[0], b"ansible")
        self.assertEqual(cipher_name, b'TEST', msg="cipher name was not set")
        self.assertEqual(vault_version, b"1.1")
        self.assertEqual(cipher_version, vault_version)

        data = b"$ANSIBLE_VAULT;1.2;TEST;3.2\nansible"
        (vault_version, cipher_name, cipher_version, rdata) = v._parse_vault_header(data)
        lines = rdata.split(b'\n')
        self.assertEqual(lines[0], b"ansible")
        self.assertEqual(cipher_name, b'TEST', msg="cipher name was not set")
        self.assertEqual(vault_version, b"1.2")
        self.assertEqual(cipher_version, b'3.2')

        data = b"$ANSIBLE_VAULT;9.9;TEST;8.9\nansible"
        (vault_version, cipher_name, cipher_version, rdata) = v._parse_vault_header(data)
        lines = rdata.split(b'\n')
        self.assertEqual(lines[0], b"ansible")
        self.assertEqual(cipher_name, b'TEST', msg="cipher name was not set")
        self.assertEqual(vault_version, b"9.9")
        self.assertEqual(cipher_version, b"8.9")


        data = b"$ANSIBLE_VAULT;1.1;TEST;3.2\nansible"
        self.assertRaisesRegexp(errors.AnsibleError, r"Malformed vault header.*3 fields.*vault 1\.1", v._parse_vault_header, data)

        data = b"$ANSIBLE_VAULT;1.2;TEST\nansible"
        self.assertRaisesRegexp(errors.AnsibleError, r"Malformed vault header.*4 fields.*vault 1\.2", v._parse_vault_header, data)

    def test_encrypt_decrypt_aes(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        # AES encryption code has been removed, so this is old output for
        # AES-encrypted 'foobar' with password 'ansible'.
        enc_data = '$ANSIBLE_VAULT;1.1;AES\n53616c7465645f5fc107ce1ef4d7b455e038a13b053225776458052f8f8f332d554809d3f150bfa3\nfe3db930508b65e0ff5947e4386b79af8ab094017629590ef6ba486814cf70f8e4ab0ed0c7d2587e\n786a5a15efeb787e1958cbdd480d076c\n'
        dec_data = v.decrypt(enc_data)[-1]
        self.assertEqual(dec_data, "foobar", msg="decryption failed")

    def test_encrypt_decrypt_aes256(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        enc_data = v.encrypt("foobar", 'AES256')
        dec_data = v.decrypt(enc_data)[-1]
        self.assertNotEqual(enc_data, "foobar", msg="encryption failed")
        self.assertEqual(dec_data, "foobar", msg="decryption failed")

    def test_encrypt_encrypted(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        data = "$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify(six.b("ansible"))
        error_hit = False
        try:
            enc_data = v.encrypt(data)
        except errors.AnsibleError as e:
            error_hit = True
        assert error_hit, "No error was thrown when trying to encrypt data with a header"

    def test_decrypt_decrypted(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        data = "ansible"
        error_hit = False
        try:
            dec_data = v.decrypt(data)
        except errors.AnsibleError as e:
            error_hit = True
        assert error_hit, "No error was thrown when trying to decrypt data without a header"

    def test_cipher_not_set(self):
        # not setting the cipher should default to AES256
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        data = "ansible"
        error_hit = False
        try:
            enc_data = v.encrypt(data)
        except errors.AnsibleError as e:
            error_hit = True
        assert not error_hit, "An error was thrown when trying to encrypt data without the cipher set"
        assert ';AES256' in enc_data, "cipher name is not set to AES256"

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
from binascii import unhexlify
from binascii import hexlify
from nose.plugins.skip import SkipTest

from ansible.compat.tests import unittest

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
                 '_add_header',
                 '_split_header',]
        for slot in slots:         
            assert hasattr(v, slot), "VaultLib is missing the %s method" % slot

    def test_is_encrypted(self):
        v = VaultLib(None)
        assert not v.is_encrypted("foobar"), "encryption check on plaintext failed"
        data = "$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify("ansible")
        assert v.is_encrypted(data), "encryption check on headered text failed"

    def test_add_header(self):
        v = VaultLib('ansible')
        v.cipher_name = "TEST"
        sensitive_data = "ansible"
        data = v._add_header(sensitive_data)
        lines = data.split('\n')
        assert len(lines) > 1, "failed to properly add header"
        header = lines[0]
        assert header.endswith(';TEST'), "header does end with cipher name"
        header_parts = header.split(';')
        assert len(header_parts) == 3, "header has the wrong number of parts"        
        assert header_parts[0] == '$ANSIBLE_VAULT', "header does not start with $ANSIBLE_VAULT"
        assert header_parts[1] == v.version, "header version is incorrect"
        assert header_parts[2] == 'TEST', "header does end with cipher name"

    def test_split_header(self):
        v = VaultLib('ansible')
        data = "$ANSIBLE_VAULT;9.9;TEST\nansible" 
        rdata = v._split_header(data)        
        lines = rdata.split('\n')
        assert lines[0] == "ansible"
        assert v.cipher_name == 'TEST', "cipher name was not set"
        assert v.version == "9.9"

    def test_encrypt_decrypt_aes(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        v.cipher_name = 'AES'
        enc_data = v.encrypt("foobar")
        dec_data = v.decrypt(enc_data)
        assert enc_data != "foobar", "encryption failed"
        assert dec_data == "foobar", "decryption failed"           

    def test_encrypt_decrypt_aes256(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        v.cipher_name = 'AES256'
        enc_data = v.encrypt("foobar")
        dec_data = v.decrypt(enc_data)
        assert enc_data != "foobar", "encryption failed"
        assert dec_data == "foobar", "decryption failed"           

    def test_encrypt_encrypted(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        v = VaultLib('ansible')
        v.cipher_name = 'AES'
        data = "$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify("ansible")
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
        assert v.cipher_name == "AES256", "cipher name is not set to AES256: %s" % v.cipher_name               

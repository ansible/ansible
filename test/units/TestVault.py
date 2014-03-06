#!/usr/bin/env python

from unittest import TestCase
import getpass
import os
import shutil
import time
import tempfile
from binascii import unhexlify
from binascii import hexlify
from nose.plugins.skip import SkipTest

from ansible import errors
from ansible.utils.vault import VaultLib
# AES IMPORTS
try:
    from Crypto.Cipher import AES as AES
    HAS_AES = True
except ImportError:
    HAS_AES = False

class TestVaultLib(TestCase):

    def test_methods_exist(self):
        v = VaultLib('ansible')
        slots = ['is_encrypted',
                 'encrypt',
                 'decrypt',
                 '_add_headers_and_hexify_encrypted_data',
                 '_split_headers_and_get_unhexified_data',]
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
        sensitive_hex = hexlify(sensitive_data)
        data = v._add_headers_and_hexify_encrypted_data(sensitive_data)
        lines = data.split('\n')
        assert len(lines) > 1, "failed to properly add header"
        header = lines[0]
        assert header.endswith(';TEST'), "header does end with cipher name"
        header_parts = header.split(';')
        assert len(header_parts) == 3, "header has the wrong number of parts"        
        assert header_parts[0] == '$ANSIBLE_VAULT', "header does not start with $ANSIBLE_VAULT"
        assert header_parts[1] == v.version, "header version is incorrect"
        assert header_parts[2] == 'TEST', "header does end with cipher name"
        assert lines[1] == sensitive_hex

    def test_remove_header(self):
        v = VaultLib('ansible')
        data = "$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify("ansible")
        rdata = v._split_headers_and_get_unhexified_data(data)        
        lines = rdata.split('\n')
        assert lines[0] == "ansible"
        assert v.cipher_name == 'TEST', "cipher name was not set"
        assert v.version == "9.9"

    def test_encyrpt_decrypt(self):
        if not HAS_AES:
            raise SkipTest
        v = VaultLib('ansible')
        v.cipher_name = 'AES'
        enc_data = v.encrypt("foobar")
        dec_data = v.decrypt(enc_data)
        assert enc_data != "foobar", "encryption failed"
        assert dec_data == "foobar", "decryption failed"           

    def test_encrypt_encrypted(self):
        if not HAS_AES:
            raise SkipTest
        v = VaultLib('ansible')
        v.cipher_name = 'AES'
        data = "$ANSIBLE_VAULT;9.9;TEST\n%s" % hexlify("ansible")
        error_hit = False
        try:
            enc_data = v.encrypt(data)
        except errors.AnsibleError, e:
            error_hit = True
        assert error_hit, "No error was thrown when trying to encrypt data with a header"    

    def test_decrypt_decrypted(self):
        if not HAS_AES:
            raise SkipTest
        v = VaultLib('ansible')
        data = "ansible"
        error_hit = False
        try:
            dec_data = v.decrypt(data)
        except errors.AnsibleError, e:
            error_hit = True
        assert error_hit, "No error was thrown when trying to decrypt data without a header"    

    def test_cipher_not_set(self):
        if not HAS_AES:
            raise SkipTest
        v = VaultLib('ansible')
        data = "ansible"
        error_hit = False
        try:
            enc_data = v.encrypt(data)
        except errors.AnsibleError, e:
            error_hit = True
        assert error_hit, "No error was thrown when trying to encrypt data without the cipher set"    

               

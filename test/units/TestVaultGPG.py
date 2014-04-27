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

#from ansible import errors
import ansible.errors
from ansible.utils.vault import VaultGPG

# GPG IMPORTS
try:
    import gnupg
    HAS_GPG = True
except ImportError:
    HAS_GPG = False

class TestVaultGPG(TestCase):

    def test_methods_exist(self):
        v = VaultGPG()
        slots = ['keys_available',
                 'encrypt',
                 'decrypt',]
        for slot in slots:         
            assert hasattr(v, slot), "VaultGPG is missing the %s method" % slot

    def test_keys_available(self):
        if not HAS_GPG:
            raise SkipTest
        v = VaultGPG()
        dirpath = tempfile.mkdtemp()
        v.pubkeyring = os.path.join(dirpath, "pubring.gpg")
        v.privkeyring = os.path.join(dirpath, "secring.gpg")
        v.alwaystrust = True # Test keyrings dont include a proper trustdb
        shutil.rmtree(dirpath)
        shutil.copytree("vault_test_data", dirpath)
        # recipients as NoneType
        try:
            enc_data = v.encrypt("foobar",'ansible')
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError
        # Empty String
        v.recipients = ''
        try:
            enc_data = v.encrypt("foobar",'ansible')
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError
        # A foriegn key ID
        v.recipients = '12341234'
        try:
            enc_data = v.encrypt("foobar",'ansible')
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError

    def test_encrypt_decrypt_gpg(self):
        if not HAS_GPG:
            raise SkipTest
        v = VaultGPG()
        dirpath = tempfile.mkdtemp()
        v.pubkeyring = os.path.join(dirpath, "pubring.gpg")
        v.privkeyring = os.path.join(dirpath, "secring.gpg")
        v.alwaystrust = True # Test keyrings dont include a proper trustdb
        shutil.rmtree(dirpath)
        shutil.copytree("vault_test_data", dirpath)
        v.recipients = '0449DF12'
        enc_data = v.encrypt("foobar",'ansible')
        dec_data = v.decrypt(enc_data,'ansible')
        assert enc_data != "foobar", "encryption failed"
        assert dec_data == "foobar", "decryption failed"

    def test_key_trust(self):
        if not HAS_GPG:
            raise SkipTest
        v = VaultGPG()
        dirpath = tempfile.mkdtemp()
        v.pubkeyring = os.path.join(dirpath, "pubring.gpg")
        v.privkeyring = os.path.join(dirpath, "secring.gpg")
        v.alwaystrust = True # Test keyrings dont include a proper trustdb
        shutil.rmtree(dirpath)
        shutil.copytree("vault_test_data", dirpath)
        # test always trusted
        v.recipients = '0449DF12 659C181E'
        enc_data = v.encrypt("foobar",'ansible')
        assert enc_data != "foobar", "encryption failed"
        # test untrusted keys fail
        v.alwaystrust = False # Test keyrings dont include a proper trustdb
        try:
            enc_data = v.encrypt("foobar",'ansible')
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError

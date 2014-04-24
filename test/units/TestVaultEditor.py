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
from ansible.utils.vault import VaultEditor

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

class TestVaultEditor(TestCase):

    def test_methods_exist(self):
        v = VaultEditor(None, None, None)
        slots = ['create_file',
                 'decrypt_file',
                 'edit_file',
                 'encrypt_file',
                 'rekey_file',
                 'read_data',
                 'write_data',
                 'shuffle_files']
        for slot in slots:         
            assert hasattr(v, slot), "VaultLib is missing the %s method" % slot

    def test_decrypt_1_0(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        dirpath = tempfile.mkdtemp()
        filename = os.path.join(dirpath, "foo-ansible-1.0.yml")
        shutil.rmtree(dirpath)
        shutil.copytree("vault_test_data", dirpath)
        ve = VaultEditor(None, "ansible", filename)

        # make sure the password functions for the cipher
        error_hit = False
        try:        
            ve.decrypt_file()
        except errors.AnsibleError, e:
            error_hit = True

        # verify decrypted content
        f = open(filename, "rb")
        fdata = f.read()
        f.close()

        shutil.rmtree(dirpath)
        assert error_hit == False, "error decrypting 1.0 file"            
        assert fdata.strip() == "foo", "incorrect decryption of 1.0 file: %s" % fdata.strip() 

    def test_decrypt_1_0_newline(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        dirpath = tempfile.mkdtemp()
        filename = os.path.join(dirpath, "foo-ansible-1.0-ansible-newline-ansible.yml")
        shutil.rmtree(dirpath)
        shutil.copytree("vault_test_data", dirpath)
        ve = VaultEditor(None, "ansible\nansible\n", filename)

        # make sure the password functions for the cipher
        error_hit = False
        try:        
            ve.decrypt_file()
        except errors.AnsibleError, e:
            error_hit = True

        # verify decrypted content
        f = open(filename, "rb")
        fdata = f.read()
        f.close()

        shutil.rmtree(dirpath)
        assert error_hit == False, "error decrypting 1.0 file with newline in password"            
        #assert fdata.strip() == "foo", "incorrect decryption of 1.0 file: %s" % fdata.strip() 


    def test_decrypt_1_1(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        dirpath = tempfile.mkdtemp()
        filename = os.path.join(dirpath, "foo-ansible-1.1.yml")
        shutil.rmtree(dirpath)
        shutil.copytree("vault_test_data", dirpath)
        ve = VaultEditor(None, "ansible", filename)

        # make sure the password functions for the cipher
        error_hit = False
        try:        
            ve.decrypt_file()
        except errors.AnsibleError, e:
            error_hit = True

        # verify decrypted content
        f = open(filename, "rb")
        fdata = f.read()
        f.close()

        shutil.rmtree(dirpath)
        assert error_hit == False, "error decrypting 1.0 file"            
        assert fdata.strip() == "foo", "incorrect decryption of 1.0 file: %s" % fdata.strip() 


    def test_rekey_migration(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest
        dirpath = tempfile.mkdtemp()
        filename = os.path.join(dirpath, "foo-ansible-1.0.yml")
        shutil.rmtree(dirpath)
        shutil.copytree("vault_test_data", dirpath)
        ve = VaultEditor(None, "ansible", filename)

        # make sure the password functions for the cipher
        error_hit = False
        try:        
            ve.rekey_file('ansible2')
        except errors.AnsibleError, e:
            error_hit = True

        # verify decrypted content
        f = open(filename, "rb")
        fdata = f.read()
        f.close()

        shutil.rmtree(dirpath)
        assert error_hit == False, "error rekeying 1.0 file to 1.1"            

        # ensure filedata can be decrypted, is 1.1 and is AES256
        vl = VaultLib("ansible2")
        dec_data = None
        error_hit = False
        try:
            dec_data = vl.decrypt(fdata)
        except errors.AnsibleError, e:
            error_hit = True

        assert vl.cipher_name == "AES256", "wrong cipher name set after rekey: %s" % vl.cipher_name
        assert error_hit == False, "error decrypting migrated 1.0 file"            
        assert dec_data.strip() == "foo", "incorrect decryption of rekeyed/migrated file: %s" % dec_data



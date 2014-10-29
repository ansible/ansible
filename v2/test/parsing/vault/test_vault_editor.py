# (c) 2014, James Tanner <tanner.jc@gmail.com>
# (c) 2014, James Cammarata, <jcammarata@ansible.com>
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
#!/usr/bin/env python

import getpass
import os
import shutil
import time
import tempfile
from binascii import unhexlify
from binascii import hexlify
from nose.plugins.skip import SkipTest

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

from ansible import errors
from ansible.parsing.vault import VaultLib
from ansible.parsing.vault import VaultEditor

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

v10_data = """$ANSIBLE_VAULT;1.0;AES
53616c7465645f5fd0026926a2d415a28a2622116273fbc90e377225c12a347e1daf4456d36a77f9
9ad98d59f61d06a4b66718d855f16fb7bdfe54d1ec8aeaa4d06c2dc1fa630ae1846a029877f0eeb1
83c62ffb04c2512995e815de4b4d29ed"""

v11_data = """$ANSIBLE_VAULT;1.1;AES256
62303130653266653331306264616235333735323636616539316433666463323964623162386137
3961616263373033353631316333623566303532663065310a393036623466376263393961326530
64336561613965383835646464623865663966323464653236343638373165343863623638316664
3631633031323837340a396530313963373030343933616133393566366137363761373930663833
3739"""

class TestVaultEditor(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

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

    @patch.object(VaultEditor, '_editor_shell_command')
    def test_create_file(self, mock_editor_shell_command):
        
        def sc_side_effect(filename):
            return ['touch', filename]
        mock_editor_shell_command.side_effect = sc_side_effect

        tmp_file = tempfile.NamedTemporaryFile()
        os.unlink(tmp_file.name)

        ve = VaultEditor(None, "ansible", tmp_file.name)
        ve.create_file()

        self.assertTrue(os.path.exists(tmp_file.name))

    def test_decrypt_1_0(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest

        v10_file = tempfile.NamedTemporaryFile(delete=False)
        with v10_file as f:
            f.write(v10_data)

        ve = VaultEditor(None, "ansible", v10_file.name)

        # make sure the password functions for the cipher
        error_hit = False
        try:
            ve.decrypt_file()
        except errors.AnsibleError as e:
            error_hit = True

        # verify decrypted content
        f = open(v10_file.name, "rb")
        fdata = f.read()
        f.close()

        os.unlink(v10_file.name)

        assert error_hit == False, "error decrypting 1.0 file"            
        assert fdata.strip() == "foo", "incorrect decryption of 1.0 file: %s" % fdata.strip() 


    def test_decrypt_1_1(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest

        v11_file = tempfile.NamedTemporaryFile(delete=False)
        with v11_file as f:
            f.write(v11_data)

        ve = VaultEditor(None, "ansible", v11_file.name)

        # make sure the password functions for the cipher
        error_hit = False
        try:
            ve.decrypt_file()
        except errors.AnsibleError as e:
            error_hit = True

        # verify decrypted content
        f = open(v11_file.name, "rb")
        fdata = f.read()
        f.close()

        os.unlink(v11_file.name)

        assert error_hit == False, "error decrypting 1.0 file"            
        assert fdata.strip() == "foo", "incorrect decryption of 1.0 file: %s" % fdata.strip() 


    def test_rekey_migration(self):
        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2:
            raise SkipTest

        v10_file = tempfile.NamedTemporaryFile(delete=False)
        with v10_file as f:
            f.write(v10_data)

        ve = VaultEditor(None, "ansible", v10_file.name)

        # make sure the password functions for the cipher
        error_hit = False
        try:        
            ve.rekey_file('ansible2')
        except errors.AnsibleError as e:
            error_hit = True

        # verify decrypted content
        f = open(v10_file.name, "rb")
        fdata = f.read()
        f.close()

        assert error_hit == False, "error rekeying 1.0 file to 1.1"            

        # ensure filedata can be decrypted, is 1.1 and is AES256
        vl = VaultLib("ansible2")
        dec_data = None
        error_hit = False
        try:
            dec_data = vl.decrypt(fdata)
        except errors.AnsibleError as e:
            error_hit = True

        os.unlink(v10_file.name)

        assert vl.cipher_name == "AES256", "wrong cipher name set after rekey: %s" % vl.cipher_name
        assert error_hit == False, "error decrypting migrated 1.0 file"            
        assert dec_data.strip() == "foo", "incorrect decryption of rekeyed/migrated file: %s" % dec_data



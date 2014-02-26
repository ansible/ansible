# (c) 2014, James Tanner <tanner.jc@gmail.com>
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
#
# ansible-pull is a script that runs ansible in local mode
# after checking out a playbooks directory from source repo.  There is an
# example playbook to bootstrap this script in the examples/ dir which
# installs ansible and sets it up to run on cron.

import os
import shutil
import tempfile
from io import BytesIO
from subprocess import call
from ansible import errors
from hashlib import sha256
from hashlib import md5
from binascii import hexlify
from binascii import unhexlify
from ansible import constants as C

# AES IMPORTS
try:
    from Crypto.Cipher import AES as AES
    HAS_AES = True   
except ImportError:
    HAS_AES = False    

HEADER='$ANSIBLE_VAULT'
CIPHER_WHITELIST=['AES']

class VaultLib(object):

    def __init__(self, password):
        self.password = password
        self.cipher_name = None
        self.version = '1.0'

    def is_encrypted(self, data): 
        if data.startswith(HEADER):
            return True
        else:
            return False

    def encrypt(self, data):

        if self.is_encrypted(data):
            raise errors.AnsibleError("data is already encrypted")

        if not self.cipher_name:
            raise errors.AnsibleError("the cipher must be set before encrypting data")

        if 'Vault' + self.cipher_name in globals() and self.cipher_name in CIPHER_WHITELIST: 
            cipher = globals()['Vault' + self.cipher_name]
            this_cipher = cipher()
        else:
            raise errors.AnsibleError("%s cipher could not be found" % self.cipher_name)

        # combine sha + data
        this_sha = sha256(data).hexdigest()
        tmp_data = this_sha + "\n" + data
        # encrypt sha + data
        tmp_data = this_cipher.encrypt(tmp_data, self.password)
        # add header 
        tmp_data = self._add_headers_and_hexify_encrypted_data(tmp_data)
        return tmp_data

    def decrypt(self, data):
        if self.password is None:
            raise errors.AnsibleError("A vault password must be specified to decrypt data")

        if not self.is_encrypted(data):
            raise errors.AnsibleError("data is not encrypted")

        # clean out header, hex and sha
        data = self._split_headers_and_get_unhexified_data(data)

        # create the cipher object
        if 'Vault' + self.cipher_name in globals() and self.cipher_name in CIPHER_WHITELIST: 
            cipher = globals()['Vault' + self.cipher_name]
            this_cipher = cipher()
        else:
            raise errors.AnsibleError("%s cipher could not be found" % self.cipher_name)

        # try to unencrypt data
        data = this_cipher.decrypt(data, self.password)

        # split out sha and verify decryption
        split_data = data.split("\n")
        this_sha = split_data[0]
        this_data = '\n'.join(split_data[1:])
        test_sha = sha256(this_data).hexdigest()
        if this_sha != test_sha:
            raise errors.AnsibleError("Decryption failed")

        return this_data            

    def _add_headers_and_hexify_encrypted_data(self, data):     
        # combine header and hexlified encrypted data in 80 char columns

        tmpdata = hexlify(data)
        tmpdata = [tmpdata[i:i+80] for i in range(0, len(tmpdata), 80)]

        if not self.cipher_name:
            raise errors.AnsibleError("the cipher must be set before adding a header")

        dirty_data = HEADER + ";" + str(self.version) + ";" + self.cipher_name + "\n"
        for l in tmpdata:
            dirty_data += l + '\n'

        return dirty_data


    def _split_headers_and_get_unhexified_data(self, data):        
        # used by decrypt

        tmpdata = data.split('\n')
        tmpheader = tmpdata[0].strip().split(';')

        self.version = str(tmpheader[1].strip())
        self.cipher_name = str(tmpheader[2].strip())
        clean_data = ''.join(tmpdata[1:])

        # strip out newline, join, unhex        
        clean_data = [ x.strip() for x in clean_data ]
        clean_data = unhexlify(''.join(clean_data))

        return clean_data

class VaultEditor(object):
    # uses helper methods for write_file(self, filename, data) 
    # to write a file so that code isn't duplicated for simple 
    # file I/O, ditto read_file(self, filename) and launch_editor(self, filename) 
    # ... "Don't Repeat Yourself", etc.

    def __init__(self, cipher_name, password, filename):
        # instantiates a member variable for VaultLib
        self.cipher_name = cipher_name
        self.password = password
        self.filename = filename

    def create_file(self):
        """ create a new encrypted file """

        if os.path.isfile(self.filename):
            raise errors.AnsibleError("%s exists, please use 'edit' instead" % self.filename)

        # drop the user into vim on file
        EDITOR = os.environ.get('EDITOR','vim')
        call([EDITOR, self.filename])
        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        this_vault.cipher_name = self.cipher_name
        enc_data = this_vault.encrypt(tmpdata)
        self.write_data(enc_data, self.filename)

    def decrypt_file(self):
        if not os.path.isfile(self.filename):
            raise errors.AnsibleError("%s does not exist" % self.filename)
        
        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        if this_vault.is_encrypted(tmpdata):
            dec_data = this_vault.decrypt(tmpdata)
            self.write_data(dec_data, self.filename)
        else:
            raise errors.AnsibleError("%s is not encrypted" % self.filename)

    def edit_file(self):

        # decrypt to tmpfile
        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        dec_data = this_vault.decrypt(tmpdata)
        _, tmp_path = tempfile.mkstemp()
        self.write_data(dec_data, tmp_path)

        # drop the user into vim on the tmp file
        EDITOR = os.environ.get('EDITOR','vim')
        call([EDITOR, tmp_path])
        new_data = self.read_data(tmp_path)

        # create new vault and set cipher to old
        new_vault = VaultLib(self.password)
        new_vault.cipher_name = this_vault.cipher_name

        # encrypt new data a write out to tmp
        enc_data = new_vault.encrypt(new_data)
        self.write_data(enc_data, tmp_path)

        # shuffle tmp file into place
        self.shuffle_files(tmp_path, self.filename)

    def encrypt_file(self):
        if not os.path.isfile(self.filename):
            raise errors.AnsibleError("%s does not exist" % self.filename)
        
        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        this_vault.cipher_name = self.cipher_name
        if not this_vault.is_encrypted(tmpdata):
            enc_data = this_vault.encrypt(tmpdata)
            self.write_data(enc_data, self.filename)
        else:
            raise errors.AnsibleError("%s is already encrypted" % self.filename)

    def rekey_file(self, new_password):
        # decrypt 
        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        dec_data = this_vault.decrypt(tmpdata)

        # create new vault, set cipher to old and password to new
        new_vault = VaultLib(new_password)
        new_vault.cipher_name = this_vault.cipher_name

        # re-encrypt data and re-write file
        enc_data = new_vault.encrypt(dec_data)
        self.write_data(enc_data, self.filename)

    def read_data(self, filename):
        f = open(filename, "rb")
        tmpdata = f.read()
        f.close()
        return tmpdata

    def write_data(self, data, filename):
        if os.path.isfile(filename): 
            os.remove(filename)
        f = open(filename, "wb")
        f.write(data)
        f.close()

    def shuffle_files(self, src, dest):
        # overwrite dest with src
        if os.path.isfile(dest):
            os.remove(dest)
        shutil.move(src, dest)

########################################
#               CIPHERS                #
########################################

class VaultAES(object):

    # http://stackoverflow.com/a/16761459

    def __init__(self):
        if not HAS_AES:
            raise errors.AnsibleError("pycrypto is not installed. Fix this with your package manager, for instance, yum-install python-crypto OR (apt equivalent)")

    def aes_derive_key_and_iv(self, password, salt, key_length, iv_length):

        """ Create a key and an initialization vector """

        d = d_i = ''
        while len(d) < key_length + iv_length:
            d_i = md5(d_i + password + salt).digest()
            d += d_i

        key = d[:key_length]
        iv = d[key_length:key_length+iv_length]

        return key, iv

    def encrypt(self, data, password, key_length=32):

        """ Read plaintext data from in_file and write encrypted to out_file """

        in_file = BytesIO(data)
        in_file.seek(0)
        out_file = BytesIO()

        bs = AES.block_size

        # Get a block of random data. EL does not have Crypto.Random.new() 
        # so os.urandom is used for cross platform purposes
        salt = os.urandom(bs - len('Salted__'))

        key, iv = self.aes_derive_key_and_iv(password, salt, key_length, bs)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        out_file.write('Salted__' + salt)
        finished = False
        while not finished:
            chunk = in_file.read(1024 * bs)
            if len(chunk) == 0 or len(chunk) % bs != 0:
                padding_length = (bs - len(chunk) % bs) or bs
                chunk += padding_length * chr(padding_length)
                finished = True
            out_file.write(cipher.encrypt(chunk))

        out_file.seek(0)
        return out_file.read()

    def decrypt(self, data, password, key_length=32):

        """ Read encrypted data from in_file and write decrypted to out_file """

        # http://stackoverflow.com/a/14989032

        in_file = BytesIO(data)
        in_file.seek(0)
        out_file = BytesIO()

        bs = AES.block_size
        salt = in_file.read(bs)[len('Salted__'):]
        key, iv = self.aes_derive_key_and_iv(password, salt, key_length, bs)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        next_chunk = ''
        finished = False

        while not finished:
            chunk, next_chunk = next_chunk, cipher.decrypt(in_file.read(1024 * bs))
            if len(next_chunk) == 0:
                padding_length = ord(chunk[-1])
                chunk = chunk[:-padding_length]
                finished = True
            out_file.write(chunk)

        # reset the stream pointer to the beginning
        out_file.seek(0)
        return out_file.read()

       

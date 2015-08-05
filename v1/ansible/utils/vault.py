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
import shlex
import shutil
import tempfile
from io import BytesIO
from subprocess import call
from ansible import errors
from hashlib import sha256

# Note: Only used for loading obsolete VaultAES files.  All files are written
# using the newer VaultAES256 which does not require md5
try:
    from hashlib import md5
except ImportError:
    try:
        from md5 import md5
    except ImportError:
        # MD5 unavailable.  Possibly FIPS mode
        md5 = None

from binascii import hexlify
from binascii import unhexlify
from ansible import constants as C

try:
    from Crypto.Hash import SHA256, HMAC
    HAS_HASH = True
except ImportError:
    HAS_HASH = False

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

CRYPTO_UPGRADE = "ansible-vault requires a newer version of pycrypto than the one installed on your platform. You may fix this with OS-specific commands such as: yum install python-devel; rpm -e --nodeps python-crypto; pip install pycrypto"

HEADER='$ANSIBLE_VAULT'
CIPHER_WHITELIST=['AES', 'AES256']

class VaultLib(object):

    def __init__(self, password):
        self.password = password
        self.cipher_name = None
        self.version = '1.1'

    def is_encrypted(self, data): 
        if data.startswith(HEADER):
            return True
        else:
            return False

    def encrypt(self, data):

        if self.is_encrypted(data):
            raise errors.AnsibleError("data is already encrypted")

        if not self.cipher_name:
            self.cipher_name = "AES256"
            #raise errors.AnsibleError("the cipher must be set before encrypting data")

        if 'Vault' + self.cipher_name in globals() and self.cipher_name in CIPHER_WHITELIST: 
            cipher = globals()['Vault' + self.cipher_name]
            this_cipher = cipher()
        else:
            raise errors.AnsibleError("%s cipher could not be found" % self.cipher_name)

        """
        # combine sha + data
        this_sha = sha256(data).hexdigest()
        tmp_data = this_sha + "\n" + data
        """

        # encrypt sha + data
        enc_data = this_cipher.encrypt(data, self.password)

        # add header 
        tmp_data = self._add_header(enc_data)
        return tmp_data

    def decrypt(self, data):
        if self.password is None:
            raise errors.AnsibleError("A vault password must be specified to decrypt data")

        if not self.is_encrypted(data):
            raise errors.AnsibleError("data is not encrypted")

        # clean out header
        data = self._split_header(data)

        # create the cipher object
        if 'Vault' + self.cipher_name in globals() and self.cipher_name in CIPHER_WHITELIST: 
            cipher = globals()['Vault' + self.cipher_name]
            this_cipher = cipher()
        else:
            raise errors.AnsibleError("%s cipher could not be found" % self.cipher_name)

        # try to unencrypt data
        data = this_cipher.decrypt(data, self.password)
        if data is None:
            raise errors.AnsibleError("Decryption failed")

        return data            

    def _add_header(self, data):     
        # combine header and encrypted data in 80 char columns

        #tmpdata = hexlify(data)
        tmpdata = [data[i:i+80] for i in range(0, len(data), 80)]

        if not self.cipher_name:
            raise errors.AnsibleError("the cipher must be set before adding a header")

        dirty_data = HEADER + ";" + str(self.version) + ";" + self.cipher_name + "\n"

        for l in tmpdata:
            dirty_data += l + '\n'

        return dirty_data


    def _split_header(self, data):        
        # used by decrypt

        tmpdata = data.split('\n')
        tmpheader = tmpdata[0].strip().split(';')

        self.version = str(tmpheader[1].strip())
        self.cipher_name = str(tmpheader[2].strip())
        clean_data = '\n'.join(tmpdata[1:])

        """
        # strip out newline, join, unhex        
        clean_data = [ x.strip() for x in clean_data ]
        clean_data = unhexlify(''.join(clean_data))
        """

        return clean_data

    def __enter__(self):
        return self

    def __exit__(self, *err):
        pass

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

    def _edit_file_helper(self, existing_data=None, cipher=None):
        # make sure the umask is set to a sane value
        old_umask = os.umask(0o077)

        # Create a tempfile
        _, tmp_path = tempfile.mkstemp()

        if existing_data:
            self.write_data(existing_data, tmp_path)

        # drop the user into an editor on the tmp file
        try:
            call(self._editor_shell_command(tmp_path))
        except OSError, e:
           raise Exception("Failed to open editor (%s): %s" % (self._editor_shell_command(tmp_path)[0],str(e)))
        tmpdata = self.read_data(tmp_path)

        # create new vault
        this_vault = VaultLib(self.password)
        if cipher:
            this_vault.cipher_name = cipher

        # encrypt new data and write out to tmp
        enc_data = this_vault.encrypt(tmpdata)
        self.write_data(enc_data, tmp_path)

        # shuffle tmp file into place
        self.shuffle_files(tmp_path, self.filename)

        # and restore umask
        os.umask(old_umask)

    def create_file(self):
        """ create a new encrypted file """

        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2 or not HAS_HASH:
            raise errors.AnsibleError(CRYPTO_UPGRADE)

        if os.path.isfile(self.filename):
            raise errors.AnsibleError("%s exists, please use 'edit' instead" % self.filename)

        # Let the user specify contents and save file
        self._edit_file_helper(cipher=self.cipher_name)

    def decrypt_file(self):

        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2 or not HAS_HASH:
            raise errors.AnsibleError(CRYPTO_UPGRADE)

        if not os.path.isfile(self.filename):
            raise errors.AnsibleError("%s does not exist" % self.filename)

        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        if this_vault.is_encrypted(tmpdata):
            dec_data = this_vault.decrypt(tmpdata)
            if dec_data is None:
                raise errors.AnsibleError("Decryption failed")
            else:
                self.write_data(dec_data, self.filename)
        else:
            raise errors.AnsibleError("%s is not encrypted" % self.filename)

    def edit_file(self):

        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2 or not HAS_HASH:
            raise errors.AnsibleError(CRYPTO_UPGRADE)

        # decrypt to tmpfile
        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        dec_data = this_vault.decrypt(tmpdata)

        # let the user edit the data and save
        self._edit_file_helper(existing_data=dec_data)
        ###we want the cipher to default to AES256 (get rid of files
        # encrypted with the AES cipher)
        #self._edit_file_helper(existing_data=dec_data, cipher=this_vault.cipher_name)


    def view_file(self):

        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2 or not HAS_HASH:
            raise errors.AnsibleError(CRYPTO_UPGRADE)

        # decrypt to tmpfile
        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        dec_data = this_vault.decrypt(tmpdata)
        old_umask = os.umask(0o077)
        _, tmp_path = tempfile.mkstemp()
        self.write_data(dec_data, tmp_path)
        os.umask(old_umask)

        # drop the user into pager on the tmp file
        call(self._pager_shell_command(tmp_path))
        os.remove(tmp_path)

    def encrypt_file(self):

        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2 or not HAS_HASH:
            raise errors.AnsibleError(CRYPTO_UPGRADE)

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

        if not HAS_AES or not HAS_COUNTER or not HAS_PBKDF2 or not HAS_HASH:
            raise errors.AnsibleError(CRYPTO_UPGRADE)

        # decrypt 
        tmpdata = self.read_data(self.filename)
        this_vault = VaultLib(self.password)
        dec_data = this_vault.decrypt(tmpdata)

        # create new vault
        new_vault = VaultLib(new_password)

        # we want to force cipher to the default
        #new_vault.cipher_name = this_vault.cipher_name

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

    def _editor_shell_command(self, filename):
        EDITOR = os.environ.get('EDITOR','vim')
        editor = shlex.split(EDITOR)
        editor.append(filename)

        return editor

    def _pager_shell_command(self, filename):
        PAGER = os.environ.get('PAGER','less')
        pager = shlex.split(PAGER)
        pager.append(filename)

        return pager

########################################
#               CIPHERS                #
########################################

class VaultAES(object):

    # this version has been obsoleted by the VaultAES256 class
    # which uses encrypt-then-mac (fixing order) and also improving the KDF used
    # code remains for upgrade purposes only
    # http://stackoverflow.com/a/16761459

    def __init__(self):
        if not md5:
            raise errors.AnsibleError('md5 hash is unavailable (Could be due to FIPS mode).  Legacy VaultAES format is unavailable.')
        if not HAS_AES:
            raise errors.AnsibleError(CRYPTO_UPGRADE)

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


        # combine sha + data
        this_sha = sha256(data).hexdigest()
        tmp_data = this_sha + "\n" + data

        in_file = BytesIO(tmp_data)
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
        enc_data = out_file.read()
        tmp_data = hexlify(enc_data)

        return tmp_data

 
    def decrypt(self, data, password, key_length=32):

        """ Read encrypted data from in_file and write decrypted to out_file """

        # http://stackoverflow.com/a/14989032

        data = ''.join(data.split('\n'))
        data = unhexlify(data)

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
        new_data = out_file.read()

        # split out sha and verify decryption
        split_data = new_data.split("\n")
        this_sha = split_data[0]
        this_data = '\n'.join(split_data[1:])
        test_sha = sha256(this_data).hexdigest()

        if this_sha != test_sha:
            raise errors.AnsibleError("Decryption failed")

        #return out_file.read()
        return this_data


class VaultAES256(object):

    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code. 
    Keys are derived using PBKDF2
    """

    # http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html

    def __init__(self):

        if not HAS_PBKDF2 or not HAS_COUNTER or not HAS_HASH:
            raise errors.AnsibleError(CRYPTO_UPGRADE)

    def gen_key_initctr(self, password, salt):
        # 16 for AES 128, 32 for AES256
        keylength = 32

        # match the size used for counter.new to avoid extra work
        ivlength = 16 

        hash_function = SHA256

        # make two keys and one iv
        pbkdf2_prf = lambda p, s: HMAC.new(p, s, hash_function).digest()


        derivedkey = PBKDF2(password, salt, dkLen=(2 * keylength) + ivlength, 
                            count=10000, prf=pbkdf2_prf)

        key1 = derivedkey[:keylength]
        key2 = derivedkey[keylength:(keylength * 2)]
        iv = derivedkey[(keylength * 2):(keylength * 2) + ivlength]

        return key1, key2, hexlify(iv)


    def encrypt(self, data, password):

        salt = os.urandom(32)
        key1, key2, iv = self.gen_key_initctr(password, salt)

        # PKCS#7 PAD DATA http://tools.ietf.org/html/rfc5652#section-6.3
        bs = AES.block_size
        padding_length = (bs - len(data) % bs) or bs
        data += padding_length * chr(padding_length)

        # COUNTER.new PARAMETERS
        # 1) nbits (integer) - Length of the counter, in bits.
        # 2) initial_value (integer) - initial value of the counter. "iv" from gen_key_initctr

        ctr = Counter.new(128, initial_value=long(iv, 16))

        # AES.new PARAMETERS
        # 1) AES key, must be either 16, 24, or 32 bytes long -- "key" from gen_key_initctr
        # 2) MODE_CTR, is the recommended mode
        # 3) counter=<CounterObject>

        cipher = AES.new(key1, AES.MODE_CTR, counter=ctr)

        # ENCRYPT PADDED DATA
        cryptedData = cipher.encrypt(data)                

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC.new(key2, cryptedData, SHA256)
        message = "%s\n%s\n%s" % ( hexlify(salt), hmac.hexdigest(), hexlify(cryptedData) )
        message = hexlify(message)
        return message

    def decrypt(self, data, password):

        # SPLIT SALT, DIGEST, AND DATA
        data = ''.join(data.split("\n"))
        data = unhexlify(data)
        salt, cryptedHmac, cryptedData = data.split("\n", 2)
        salt = unhexlify(salt)
        cryptedData = unhexlify(cryptedData)

        key1, key2, iv = self.gen_key_initctr(password, salt)

        # EXIT EARLY IF DIGEST DOESN'T MATCH 
        hmacDecrypt = HMAC.new(key2, cryptedData, SHA256)
        if not self.is_equal(cryptedHmac, hmacDecrypt.hexdigest()):
            return None

        # SET THE COUNTER AND THE CIPHER
        ctr = Counter.new(128, initial_value=long(iv, 16))
        cipher = AES.new(key1, AES.MODE_CTR, counter=ctr)

        # DECRYPT PADDED DATA
        decryptedData = cipher.decrypt(cryptedData)

        # UNPAD DATA
        padding_length = ord(decryptedData[-1])
        decryptedData = decryptedData[:-padding_length]

        return decryptedData

    def is_equal(self, a, b):
        # http://codahale.com/a-lesson-in-timing-attacks/
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0     



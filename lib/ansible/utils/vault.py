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
    from Crypto.Cipher import AES as AES_
    HAS_AES = True   
except ImportError:
    HAS_AES = False    

HEADER='$ANSIBLE_VAULT'

def is_encrypted(filename):

    ''' 
    Check a file for the encrypted header and return True or False 
    
    The first line should start with the header
    defined by the global HEADER. If true, we 
    assume this is a properly encrypted file.
    '''

    # read first line of the file
    with open(filename) as f:
        head = f.next()

    if head.startswith(HEADER):
        return True
    else:
        return False

def decrypt(filename, password):

    ''' 
    Return a decrypted string of the contents in an encrypted file

    This is used by the yaml loading code in ansible
    to automatically determine the encryption type
    and return a plaintext string of the unencrypted
    data.  
    '''

    if password is None:
        raise errors.AnsibleError("A vault password must be specified to decrypt %s" % filename)

    V = Vault(filename=filename, vault_password=password)
    return_data = V._decrypt_to_string()

    if not V._verify_decryption(return_data):
        raise errors.AnsibleError("Decryption of %s failed" % filename)

    this_sha, return_data = V._strip_sha(return_data)    
    return return_data.strip()


class Vault(object):
    def __init__(self, filename=None, cipher=None, vault_password=None):
        self.filename = filename
        self.vault_password = vault_password
        self.cipher = cipher
        self.version = '1.0'

    ###############
    #   PUBLIC
    ###############

    def eval_header(self):

        """ Read first line of the file and parse header """

        # read first line
        with open(self.filename) as f:
            #head=[f.next() for x in xrange(1)]
            head = f.next()

        this_version = None
        this_cipher = None

        # split segments
        if len(head.split(';')) == 3:
            this_version = head.split(';')[1].strip()
            this_cipher = head.split(';')[2].strip()            
        else:
            raise errors.AnsibleError("%s has an invalid header" % self.filename)

        # validate acceptable version
        this_version = float(this_version)
        if this_version < C.VAULT_VERSION_MIN or this_version > C.VAULT_VERSION_MAX:
            raise errors.AnsibleError("%s must have a version between %s and %s " % (self.filename, 
                                                                            C.VAULT_VERSION_MIN,
                                                                            C.VAULT_VERSION_MAX))
        # set properties
        self.cipher = this_cipher
        self.version = this_version

    def create(self):
        """ create a new encrypted file """

        if os.path.isfile(self.filename):
            raise errors.AnsibleError("%s exists, please use 'edit' instead" % self.filename)

        # drop the user into vim on file
        EDITOR = os.environ.get('EDITOR','vim')
        call([EDITOR, self.filename])

        self.encrypt()

    def decrypt(self):
        """ unencrypt a file inplace """

        if not is_encrypted(self.filename):
            raise errors.AnsibleError("%s is not encrypted" % self.filename)

        # set cipher based on file header
        self.eval_header()

        # decrypt it
        data = self._decrypt_to_string()

        # verify sha and then strip it out
        if not self._verify_decryption(data):
            raise errors.AnsibleError("decryption of %s failed" % self.filename)
        this_sha, clean_data = self._strip_sha(data)
        
        # write back to original file
        f = open(self.filename, "wb")
        f.write(clean_data)
        f.close()

    def edit(self, filename=None, password=None, cipher=None, version=None):

        if not is_encrypted(self.filename):
            raise errors.AnsibleError("%s is not encrypted" % self.filename)

        #decrypt to string
        data = self._decrypt_to_string()

        # verify sha and then strip it out
        if not self._verify_decryption(data):
            raise errors.AnsibleError("decryption of %s failed" % self.filename)
        this_sha, clean_data = self._strip_sha(data)

        # rewrite file without sha        
        _, in_path = tempfile.mkstemp()
        f = open(in_path, "wb")
        tmpdata = f.write(clean_data)
        f.close()

        # drop the user into vim on the unencrypted tmp file
        EDITOR = os.environ.get('EDITOR','vim')
        call([EDITOR, in_path])

        f = open(in_path, "rb")
        tmpdata = f.read()
        f.close()

        self._string_to_encrypted_file(tmpdata, self.filename)


    def encrypt(self):
        """ encrypt a file inplace """

        if is_encrypted(self.filename):
            raise errors.AnsibleError("%s is already encrypted" % self.filename)

        #self.eval_header()
        self.__load_cipher()

        # read data
        f = open(self.filename, "rb")
        tmpdata = f.read()
        f.close()

        self._string_to_encrypted_file(tmpdata, self.filename)


    def rekey(self, newpassword):

        """ unencrypt file then encrypt with new password """

        if not is_encrypted(self.filename):
            raise errors.AnsibleError("%s is not encrypted" % self.filename)

        # unencrypt to string with old password
        data = self._decrypt_to_string()

        # verify sha and then strip it out
        if not self._verify_decryption(data):
            raise errors.AnsibleError("decryption of %s failed" % self.filename)
        this_sha, clean_data = self._strip_sha(data)
    
        # set password     
        self.vault_password = newpassword

        self._string_to_encrypted_file(clean_data, self.filename)


    ###############
    #   PRIVATE
    ###############

    def __load_cipher(self):

        """ 
        Load a cipher class by it's name

        This is a lightweight "plugin" implementation to allow
        for future support of other cipher types
        """

        whitelist = ['AES']

        if self.cipher in whitelist:
            self.cipher_obj = None
            if self.cipher in globals():
                this_cipher = globals()[self.cipher]
                self.cipher_obj = this_cipher()
            else:
                raise errors.AnsibleError("%s cipher could not be loaded" % self.cipher)
        else:
            raise errors.AnsibleError("%s is not an allowed encryption cipher" % self.cipher)



    def _decrypt_to_string(self):

        """ decrypt file to string """

        if not is_encrypted(self.filename):
            raise errors.AnsibleError("%s is not encrypted" % self.filename)

        # figure out what this is
        self.eval_header()
        self.__load_cipher()

        # strip out header and unhex the file
        clean_stream = self._dirty_file_to_clean_file(self.filename)

        # reset pointer
        clean_stream.seek(0)

        # create a byte stream to hold unencrypted
        dst = BytesIO()

        # decrypt from src stream to dst stream
        self.cipher_obj.decrypt(clean_stream, dst, self.vault_password)

        # read data from the unencrypted stream
        data = dst.read()

        return data 

    def _dirty_file_to_clean_file(self, dirty_filename):
        """ Strip out headers from a file, unhex and write to new file"""


        _, in_path = tempfile.mkstemp()
        #_, out_path = tempfile.mkstemp()

        # strip header from data, write rest to tmp file
        f = open(dirty_filename, "rb")
        tmpdata = f.readlines()
        f.close()

        tmpheader = tmpdata[0].strip()
        tmpdata = ''.join(tmpdata[1:])

        # strip out newline, join, unhex        
        tmpdata = [ x.strip() for x in tmpdata ]
        tmpdata = unhexlify(''.join(tmpdata))

        # create and return stream
        clean_stream = BytesIO(tmpdata)
        return clean_stream

    def _clean_stream_to_dirty_stream(self, clean_stream):
 
        # combine header and hexlified encrypted data in 80 char columns
        clean_stream.seek(0)
        tmpdata = clean_stream.read()
        tmpdata = hexlify(tmpdata)
        tmpdata = [tmpdata[i:i+80] for i in range(0, len(tmpdata), 80)]

        dirty_data = HEADER + ";" + str(self.version) + ";" + self.cipher + "\n"
        for l in tmpdata:
            dirty_data += l + '\n'

        dirty_stream = BytesIO(dirty_data)
        return dirty_stream

    def _string_to_encrypted_file(self, tmpdata, filename):

        """ Write a string of data to a file with the format ...

        HEADER;VERSION;CIPHER
        HEX(ENCRYPTED(SHA256(STRING)+STRING))
        """

        # sha256 the data
        this_sha = sha256(tmpdata).hexdigest()

        # combine sha + data to tmpfile
        tmpdata = this_sha + "\n" + tmpdata 
        src_stream = BytesIO(tmpdata)
        dst_stream = BytesIO()

        # encrypt tmpfile
        self.cipher_obj.encrypt(src_stream, dst_stream, self.password)

        # hexlify tmpfile and combine with header
        dirty_stream = self._clean_stream_to_dirty_stream(dst_stream)

        if os.path.isfile(filename):
            os.remove(filename)
        
        # write back to original file
        dirty_stream.seek(0)
        f = open(filename, "wb")
        f.write(dirty_stream.read())
        f.close()


    def _verify_decryption(self, data):

        """ Split data to sha/data and check the sha """

        # split the sha and other data
        this_sha, clean_data = self._strip_sha(data)

        # does the decrypted data match the sha ?
        clean_sha = sha256(clean_data).hexdigest()
       
        # compare, return result 
        if this_sha == clean_sha:
            return True
        else:
            return False

    def _strip_sha(self, data):
        # is the first line a sha?
        lines = data.split("\n")
        this_sha = lines[0]

        clean_data = '\n'.join(lines[1:])
        return this_sha, clean_data       


class AES(object):

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

    def encrypt(self, in_file, out_file, password, key_length=32):

        """ Read plaintext data from in_file and write encrypted to out_file """

        bs = AES_.block_size

        # Get a block of random data. EL does not have Crypto.Random.new() 
        # so os.urandom is used for cross platform purposes
        print "WARNING: if encryption hangs, add more entropy (suggest using mouse inputs)"
        salt = os.urandom(bs - len('Salted__'))

        key, iv = self.aes_derive_key_and_iv(password, salt, key_length, bs)
        cipher = AES_.new(key, AES_.MODE_CBC, iv)
        out_file.write('Salted__' + salt)
        finished = False
        while not finished:
            chunk = in_file.read(1024 * bs)
            if len(chunk) == 0 or len(chunk) % bs != 0:
                padding_length = (bs - len(chunk) % bs) or bs
                chunk += padding_length * chr(padding_length)
                finished = True
            out_file.write(cipher.encrypt(chunk))

    def decrypt(self, in_file, out_file, password, key_length=32):

        """ Read encrypted data from in_file and write decrypted to out_file """

        # http://stackoverflow.com/a/14989032

        bs = AES_.block_size
        salt = in_file.read(bs)[len('Salted__'):]
        key, iv = self.aes_derive_key_and_iv(password, salt, key_length, bs)
        cipher = AES_.new(key, AES_.MODE_CBC, iv)
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
        if hasattr(out_file, 'seek'):
            out_file.seek(0)

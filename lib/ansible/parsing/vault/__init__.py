# (c) 2014, James Tanner <tanner.jc@gmail.com>
# Copyright 2015 Abhijit Menon-Sen <ams@2ndQuadrant.com>
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

import os
import shlex
import shutil
import sys
import tempfile
import base64
from io import BytesIO
from subprocess import call
from ansible.errors import AnsibleError
from hashlib import sha256
from binascii import hexlify
from binascii import unhexlify
from six import PY3

# Note: Only used for loading obsolete VaultAES files.  All files are written
# using the newer VaultAES256 which does not require md5
from hashlib import md5


try:
    from six import byte2int
except ImportError:
    # bytes2int added in six-1.4.0
    if PY3:
        import operator
        byte2int = operator.itemgetter(0)
    else:
        def byte2int(bs):
            return ord(bs[0])

from ansible.utils.unicode import to_unicode, to_bytes


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

# OpenSSL pbkdf2_hmac
HAS_PBKDF2HMAC = False
try:
    from cryptography.hazmat.primitives.hashes import SHA256 as c_SHA256
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    HAS_PBKDF2HMAC = True
except ImportError:
    pass

HAS_ANY_PBKDF2HMAC = HAS_PBKDF2 or HAS_PBKDF2HMAC

CRYPTO_UPGRADE = "ansible-vault requires a newer version of pycrypto than the one installed on your platform. You may fix this with OS-specific commands such as: yum install python-devel; rpm -e --nodeps python-crypto; pip install pycrypto"

b_HEADER = b'$ANSIBLE_VAULT'
CIPHER_WHITELIST = frozenset((u'AES', u'AES256'))
CIPHER_WRITE_WHITELIST=frozenset((u'AES256',))
DEFAULT_WRITE_CIPHER=u'AES256'


def check_prereqs():

    if not HAS_AES or not HAS_COUNTER or not HAS_ANY_PBKDF2HMAC or not HAS_HASH:
        raise AnsibleError(CRYPTO_UPGRADE)

class VaultLib:

    def __init__(self, password):
        self.b_password = to_bytes(password, errors='strict', encoding='utf-8')

    def is_encrypted(self, data):
        """ Test if this is vault encrypted data

        :arg data: a byte str or unicode string to test whether it is
            recognized as vault encrypted data
        :returns: True if it is recognized.  Otherwise, False.
        """

        if to_bytes(data, errors='strict', encoding='utf-8').startswith(b_HEADER):
            return True
        return False

    def _cipher(self, cipher_name):
        """
        Takes a cipher name and returns a Vault cipher class.
        """

        cipher_class_name = u'Vault{0}'.format(cipher_name)
        if cipher_class_name in globals():
            Cipher = globals()[cipher_class_name]
        else:
            raise AnsibleError(u"{0} cipher could not be found".format(cipher_name))

        return Cipher

    def _add_vault_header(self, cipher_name, cipher_version, b_ciphertext):
        """
        Takes a cipher name and version and ciphertext (formatted output from a
        cipher class) and returns a byte string containing the vault header and
        the unmodified ciphertext.

        :arg cipher_name: cipher name as a unicode string
        :arg version: cipher version as a unicode string
        :arg b_data: the formatted ciphertext as a byte string
        :returns: a byte string that can be dumped into a file.
        """

        b_vault_version = b'1.2'
        b_cipher_name = to_bytes(cipher_name, errors='strict', encoding='utf-8')
        b_cipher_version = to_bytes(cipher_version, errors='strict', encoding='utf-8')
        b_data = b'%s;%s;%s;%s\n%s' % \
            (b_HEADER, b_vault_version, b_cipher_name, b_cipher_version, b_ciphertext)

        return b_data

    def _parse_vault_header(self, data):
        """
        Takes the contents of a vault-encrypted file (i.e. the output of
        _add_vault_header) and returns the vault metadata and ciphertext.

        :arg data: vault file contents. Since vault encrypted data is an ascii
            text format this can be either a byte str or unicode string.
        :returns: vault version as unicode, cipher name as unicode, cipher
            version as unicode, and ciphertext as a byte str. If any of the
            above is None, the header is not valid.
        """

        b_data = to_bytes(data, errors='strict', encoding='utf-8')

        lines = b_data.split(b'\n', 1)
        header = lines[0].strip().split(b';')

        vault_version = None
        cipher_name = None
        cipher_version = None
        b_data = None

        if len(header) >= 3 and header[0] == b_HEADER:
            vault_version = to_unicode(header[1].strip())
            cipher_name = to_unicode(header[2].strip())
            if vault_version == u'1.2' and len(header) == 4:
                cipher_version = to_unicode(header[3].strip())
            elif len(header) == 3:
                cipher_version = vault_version

        if len(lines) > 1:
            b_data = lines[1]

        return (vault_version, cipher_name, cipher_version, b_data)

    def encrypt(self, data, cipher_name=None):
        """
        Takes plaintext as a unicode string, encrypts it using the specified (or
        default) cipher, and returns the vault header and ciphertext as a byte
        string suitable to be written as-is to a vault file.

        :arg data: a utf-8 byte str or unicode string to encrypt.
        :returns: a utf-8 encoded byte str of encrypted data.
        """
        b_plaintext = to_bytes(data, errors='strict', encoding='utf-8')

        if self.is_encrypted(b_plaintext):
            raise AnsibleError("input is already encrypted")

        if not cipher_name or cipher_name not in CIPHER_WRITE_WHITELIST:
            cipher_name = DEFAULT_WRITE_CIPHER

        cipher = self._cipher(cipher_name)()

        b_ciphertext = cipher.encrypt(b_plaintext, self.b_password)
        b_data = self._add_vault_header(cipher_name, cipher.version, b_ciphertext)

        return b_data

    def decrypt_with_metadata(self, data):
        """
        Takes the contents of a vault file (i.e. header and ciphertext) and
        returns the cipher name and version along with the plaintext.

        :arg data: vault file contents. Since vault encrypted data is an ascii
            text format this can be either a byte str or unicode string.
        :returns: cipher name and cipher version as unicode, plaintext as
            a byte str
        """
        if self.b_password is None:
            raise AnsibleError("A vault password must be specified to decrypt data")

        _, cipher_name, cipher_version, b_ciphertext = self._parse_vault_header(data)

        if not cipher_name:
            raise AnsibleError("input is not encrypted")

        if not cipher_name in CIPHER_WHITELIST:
            raise AnsibleError("Vault file encrypted with unrecognised cipher: {0}".format(cipher_name))

        cipher = self._cipher(cipher_name)()

        b_plaintext = cipher.decrypt(b_ciphertext, self.b_password, version=cipher_version)
        if b_plaintext is None:
            raise AnsibleError("Decryption failed")

        return cipher_name, cipher_version, b_plaintext

    def decrypt(self, data):
        """
        Takes the contents of a vault file (i.e. header and ciphertext) and
        returns the plaintext.

        :arg data: vault file contents. Since vault encrypted data is an ascii
            text format this can be either a byte str or unicode string.
        :returns: plaintext as a byte str
        """

        _, _, b_plaintext = self.decrypt_with_metadata(data)

        return b_plaintext

class VaultEditor:

    def __init__(self, password):
        self.vault = VaultLib(password)

    def _edit_file_helper(self, filename, existing_data=None, force_save=False):
        # make sure the umask is set to a sane value
        old_umask = os.umask(0o077)

        # Create a tempfile
        _, tmp_path = tempfile.mkstemp()

        if existing_data:
            self.write_data(existing_data, tmp_path)

        # drop the user into an editor on the tmp file
        call(self._editor_shell_command(tmp_path))
        tmpdata = self.read_data(tmp_path)

        # Do nothing if the content has not changed
        if existing_data == tmpdata and not force_save:
            os.remove(tmp_path)
            return

        # encrypt new data and write out to tmp
        enc_data = self.vault.encrypt(tmpdata)
        self.write_data(enc_data, tmp_path)

        # shuffle tmp file into place
        self.shuffle_files(tmp_path, filename)

        # and restore umask
        os.umask(old_umask)

    def encrypt_file(self, filename, output_file=None):

        check_prereqs()

        plaintext = self.read_data(filename)
        ciphertext = self.vault.encrypt(plaintext)
        self.write_data(ciphertext, output_file or filename)

    def decrypt_file(self, filename, output_file=None):

        check_prereqs()

        ciphertext = self.read_data(filename)
        plaintext = self.vault.decrypt(ciphertext)
        self.write_data(plaintext, output_file or filename)

    def create_file(self, filename):
        """ create a new encrypted file """

        check_prereqs()

        # FIXME: If we can raise an error here, we can probably just make it
        # behave like edit instead.
        if os.path.isfile(filename):
            raise AnsibleError("%s exists, please use 'edit' instead" % filename)

        self._edit_file_helper(filename)

    def edit_file(self, filename):

        check_prereqs()

        ciphertext = self.read_data(filename)
        cipher_name, cipher_version, plaintext = self.vault.decrypt_with_metadata(ciphertext)

        if cipher_name not in CIPHER_WRITE_WHITELIST:
            # we want to get rid of files encrypted with the AES cipher
            self._edit_file_helper(filename, existing_data=plaintext, force_save=True)
        else:
            self._edit_file_helper(filename, existing_data=plaintext, force_save=False)

    def plaintext(self, filename):

        check_prereqs()

        ciphertext = self.read_data(filename)
        plaintext = self.vault.decrypt(ciphertext)

        return plaintext

    def rekey_file(self, filename, new_password):

        check_prereqs()

        ciphertext = self.read_data(filename)
        plaintext = self.vault.decrypt(ciphertext)

        new_vault = VaultLib(new_password)
        new_ciphertext = new_vault.encrypt(plaintext)
        self.write_data(new_ciphertext, filename)

    def read_data(self, filename):
        try:
            if filename == '-':
                data = sys.stdin.read()
            else:
                with open(filename, "rb") as fh:
                    data = fh.read()
        except Exception as e:
            raise AnsibleError(str(e))

        return data

    def write_data(self, data, filename):
        bytes = to_bytes(data, errors='strict')
        if filename == '-':
            sys.stdout.write(bytes)
        else:
            if os.path.isfile(filename):
                os.remove(filename)
            with open(filename, "wb") as fh:
                fh.write(bytes)

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

class VaultFile(object):

    def __init__(self, password, filename):
        self.password = password

        self.filename = filename
        if not os.path.isfile(self.filename):
            raise AnsibleError("%s does not exist" % self.filename)
        try:
            self.filehandle = open(filename, "rb")
        except Exception as e:
            raise AnsibleError("Could not open %s: %s" % (self.filename, str(e)))

        _, self.tmpfile = tempfile.mkstemp()

    ### FIXME:
    # __del__ can be problematic in python... For this use case, make
    # VaultFile a context manager instead (implement __enter__ and __exit__)
    def __del__(self):
        self.filehandle.close()
        os.unlink(self.tmplfile)

    def is_encrypted(self):
        peak = self.filehandle.readline()
        if peak.startswith(b_HEADER):
            return True
        else:
            return False

    def get_decrypted(self):
        check_prereqs()

        if self.is_encrypted():
            tmpdata = self.filehandle.read()
            this_vault = VaultLib(self.password)
            dec_data = this_vault.decrypt(tmpdata)
            if dec_data is None:
                raise AnsibleError("Decryption failed")
            else:
                self.tmpfile.write(dec_data)
                return self.tmpfile
        else:
            return self.filename

########################################
#               CIPHERS                #
########################################

class VaultAES:

    # this version has been obsoleted by the VaultAES256 class
    # which uses encrypt-then-mac (fixing order) and also improving the KDF used
    # code remains for upgrade purposes only
    # http://stackoverflow.com/a/16761459

    # Note: strings in this class should be byte strings by default.

    def __init__(self):
        if not HAS_AES:
            raise AnsibleError(CRYPTO_UPGRADE)
        self.version = u'1.1'

    def aes_derive_key_and_iv(self, password, salt, key_length, iv_length):

        """ Create a key and an initialization vector """

        d = d_i = b''
        while len(d) < key_length + iv_length:
            text = b"%s%s%s" % (d_i, password, salt)
            d_i = to_bytes(md5(text).digest(), errors='strict')
            d += d_i

        key = d[:key_length]
        iv = d[key_length:key_length+iv_length]

        return key, iv

    def encrypt(self, data, password, key_length=32):

        """ Read plaintext data from in_file and write encrypted to out_file """

        raise AnsibleError("Encryption disabled for deprecated VaultAES class")

    def decrypt(self, data, password, key_length=32, version=None):

        """ Read encrypted data from in_file and write decrypted to out_file """

        # http://stackoverflow.com/a/14989032

        data = unhexlify(data.replace(b'\n',''))

        in_file = BytesIO(data)
        in_file.seek(0)
        out_file = BytesIO()

        bs = AES.block_size
        tmpsalt = in_file.read(bs)
        salt = tmpsalt[len(b'Salted__'):]
        key, iv = self.aes_derive_key_and_iv(password, salt, key_length, bs)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        next_chunk = b''
        finished = False

        while not finished:
            chunk, next_chunk = next_chunk, cipher.decrypt(in_file.read(1024 * bs))
            if len(next_chunk) == 0:
                if PY3:
                    padding_length = chunk[-1]
                else:
                    padding_length = ord(chunk[-1])

                chunk = chunk[:-padding_length]
                finished = True

            out_file.write(chunk)
            out_file.flush()

        # reset the stream pointer to the beginning
        out_file.seek(0)
        out_data = out_file.read()
        out_file.close()

        # split out sha and verify decryption
        split_data = out_data.split(b"\n", 1)
        this_sha = split_data[0]
        this_data = split_data[1]
        test_sha = to_bytes(sha256(this_data).hexdigest())

        if this_sha != test_sha:
            raise AnsibleError("Decryption failed")

        return this_data


class VaultAES256:

    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2
    """

    # http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html

    # Note: strings in this class should be byte strings by default.

    def __init__(self):

        check_prereqs()

        self.version = u'1.2'

    def create_key(self, password, salt, keylength, ivlength):
        hash_function = SHA256

        # make two keys and one iv
        pbkdf2_prf = lambda p, s: HMAC.new(p, s, hash_function).digest()

        derivedkey = PBKDF2(password, salt, dkLen=(2 * keylength) + ivlength,
                            count=10000, prf=pbkdf2_prf)
        return derivedkey

    def gen_key_initctr(self, password, salt, generate_iv=False):
        '''
        Takes a password and random 32-byte salt and stretches it using
        PBKDF2 into an 32-byte AES key, a 32-byte HMAC-SHA-256 key, and
        (optionally) a 16-byte IV for AES-CTR.

        The initial value for the counter is zero by default, but we support
        generating a value using PBKDF2 for backwards compatibility.

        CTR mode requires that the same key and the same counter are only ever
        used once to encrypt data. Since we generate the key using a random salt
        each time, the initial counter value can be 0. Using PBKDF2 to generate
        the value just slows things down (specifically, it adds 10000 iterations
        of the PRF, and then throws half of the 32-byte output away).
        '''
        # 16 for AES 128, 32 for AES256
        keylength = 32

        # match the size used for counter.new to avoid extra work
        ivlength = 0
        if generate_iv:
            ivlength = 16

        if HAS_PBKDF2HMAC:
            backend = default_backend()
            kdf = PBKDF2HMAC(
                algorithm=c_SHA256(),
                length=2 * keylength + ivlength,
                salt=salt,
                iterations=10000,
                backend=backend)
            derivedkey = kdf.derive(password)
        else:
            derivedkey = self.create_key(password, salt, keylength, ivlength)

        key1 = derivedkey[:keylength]
        key2 = derivedkey[keylength:(keylength * 2)]

        iv = 0
        if generate_iv:
            iv = derivedkey[(keylength * 2):(keylength * 2) + ivlength]
            iv = int(hexlify(iv), 16)

        return key1, key2, iv


    def encrypt(self, plaintext, password):

        salt = os.urandom(32)
        key1, key2, iv = self.gen_key_initctr(password, salt)

        # COUNTER.new PARAMETERS
        # 1) nbits (integer) - Length of the counter, in bits.
        # 2) initial_value (integer) - initial value of the counter. "iv" from gen_key_initctr

        ctr = Counter.new(128, initial_value=iv)

        # AES.new PARAMETERS
        # 1) AES key, must be either 16, 24, or 32 bytes long -- "key" from gen_key_initctr
        # 2) MODE_CTR, is the recommended mode
        # 3) counter=<CounterObject>

        cipher = AES.new(key1, AES.MODE_CTR, counter=ctr)

        ciphertext = cipher.encrypt(plaintext)
        hmac = HMAC.new(key2, ciphertext, SHA256)

        message = base64.b64encode(salt+hmac.digest()+ciphertext)
        lines = [b'%s\n' % message[i:i+80] for i in range(0, len(message), 80)]
        data = ''.join(lines)

        return data

    def decrypt(self, message, password, version=None):

        message = message.replace(b'\n', '')

        if version == u'1.1':
            message = unhexlify(message)
            salt, mac, ciphertext = message.split(b'\n', 2)
            salt = unhexlify(salt)
            mac = unhexlify(mac)
            ciphertext = unhexlify(ciphertext)
            key1, key2, iv = self.gen_key_initctr(password, salt, generate_iv=True)
        else:
            message = base64.b64decode(message)
            salt = message[0:32]
            mac = message[32:64]
            ciphertext = message[64:]
            key1, key2, iv = self.gen_key_initctr(password, salt)

        # EXIT EARLY IF MAC DOESN'T VALIDATE
        hmac = HMAC.new(key2, ciphertext, SHA256)
        if not self.is_equal(mac, to_bytes(hmac.digest())):
            return None

        # SET THE COUNTER AND THE CIPHER
        ctr = Counter.new(128, initial_value=iv)
        cipher = AES.new(key1, AES.MODE_CTR, counter=ctr)

        plaintext = cipher.decrypt(ciphertext)

        # We used spurious padding in v1.1, which we must remove.
        if version == u'1.1':
            try:
                padding_length = ord(plaintext[-1])
            except TypeError:
                padding_length = plaintext[-1]

            plaintext = plaintext[:-padding_length]

        return plaintext

    def is_equal(self, a, b):
        """
        Comparing 2 byte arrrays in constant time
        to avoid timing attacks.

        It would be nice if there was a library for this but
        hey.
        """
        # http://codahale.com/a-lesson-in-timing-attacks/
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b):
            if PY3:
                result |= x ^ y
            else:
                result |= ord(x) ^ ord(y)
        return result == 0


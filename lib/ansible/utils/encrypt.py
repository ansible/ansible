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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os
import stat
import time
import warnings

PASSLIB_AVAILABLE = False
try:
    import passlib.hash
    PASSLIB_AVAILABLE = True
except:
    pass

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

KEYCZAR_AVAILABLE=False
try:
    try:
        # some versions of pycrypto may not have this?
        from Crypto.pct_warnings import PowmInsecureWarning
    except ImportError:
        PowmInsecureWarning = RuntimeWarning

    with warnings.catch_warnings(record=True) as warning_handler:
        warnings.simplefilter("error", PowmInsecureWarning)
        try:
            import keyczar.errors as key_errors
            from keyczar.keys import AesKey
        except PowmInsecureWarning:
            display.system_warning(
                "The version of gmp you have installed has a known issue regarding " + \
                "timing vulnerabilities when used with pycrypto. " + \
                "If possible, you should update it (i.e. yum update gmp)."
            )
            warnings.resetwarnings()
            warnings.simplefilter("ignore")
            import keyczar.errors as key_errors
            from keyczar.keys import AesKey
        KEYCZAR_AVAILABLE=True
except ImportError:
    pass

from ansible import constants as C
from ansible.errors import AnsibleError

__all__ = ['do_encrypt']

def do_encrypt(result, encrypt, salt_size=None, salt=None):
    if PASSLIB_AVAILABLE:
        try:
            crypt = getattr(passlib.hash, encrypt)
        except:
            raise AnsibleError("passlib does not support '%s' algorithm" % encrypt)

        if salt_size:
            result = crypt.encrypt(result, salt_size=salt_size)
        elif salt:
            result = crypt.encrypt(result, salt=salt)
        else:
            result = crypt.encrypt(result)
    else:
        raise AnsibleError("passlib must be installed to encrypt vars_prompt values")

    return result

def key_for_hostname(hostname):
    # fireball mode is an implementation of ansible firing up zeromq via SSH
    # to use no persistent daemons or key management

    if not KEYCZAR_AVAILABLE:
        raise AnsibleError("python-keyczar must be installed on the control machine to use accelerated modes")

    key_path = os.path.expanduser(C.ACCELERATE_KEYS_DIR)
    if not os.path.exists(key_path):
        os.makedirs(key_path, mode=0o700)
        os.chmod(key_path, int(C.ACCELERATE_KEYS_DIR_PERMS, 8))
    elif not os.path.isdir(key_path):
        raise AnsibleError('ACCELERATE_KEYS_DIR is not a directory.')

    if stat.S_IMODE(os.stat(key_path).st_mode) != int(C.ACCELERATE_KEYS_DIR_PERMS, 8):
        raise AnsibleError('Incorrect permissions on the private key directory. Use `chmod 0%o %s` to correct this issue, and make sure any of the keys files contained within that directory are set to 0%o' % (int(C.ACCELERATE_KEYS_DIR_PERMS, 8), C.ACCELERATE_KEYS_DIR, int(C.ACCELERATE_KEYS_FILE_PERMS, 8)))

    key_path = os.path.join(key_path, hostname)

    # use new AES keys every 2 hours, which means fireball must not allow running for longer either
    if not os.path.exists(key_path) or (time.time() - os.path.getmtime(key_path) > 60*60*2):
        key = AesKey.Generate(size=256)
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT, int(C.ACCELERATE_KEYS_FILE_PERMS, 8))
        fh = os.fdopen(fd, 'w')
        fh.write(str(key))
        fh.close()
        return key
    else:
        if stat.S_IMODE(os.stat(key_path).st_mode) != int(C.ACCELERATE_KEYS_FILE_PERMS, 8):
            raise AnsibleError('Incorrect permissions on the key file for this host. Use `chmod 0%o %s` to correct this issue.' % (int(C.ACCELERATE_KEYS_FILE_PERMS, 8), key_path))
        fh = open(key_path)
        key = AesKey.Read(fh.read())
        fh.close()
        return key

def keyczar_encrypt(key, msg):
    return key.Encrypt(msg.encode('utf-8'))

def keyczar_decrypt(key, msg):
    try:
        return key.Decrypt(msg)
    except key_errors.InvalidSignatureError:
        raise AnsibleError("decryption failed")


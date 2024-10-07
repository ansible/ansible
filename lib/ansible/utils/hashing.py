# Copyright: Contributors to the Ansible project
# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import os

from hashlib import sha1, sha256

try:
    from hashlib import md5 as _md5
except ImportError:
    # Assume we're running in FIPS mode here
    _md5 = None

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_bytes


def generate_secure_checksum(data, hash_func=sha256):
    """Generates a secure checksum for the given data using the specified hash function.

    Args:
        data: The data to be hashed.
        hash_func: The hash function to use (default: hashlib.sha256).

    Returns:
        A hexadecimal string representing the checksum.
    """

    digest = hash_func()
    data = to_bytes(data, errors='surrogate_or_strict')
    digest.update(data)
    return digest.hexdigest()


def generate_secure_file_checksum(filename, hash_func=sha256):
    """Return a secure hash hex digest of local file, None if file is not present or a directory.

    Args:
        filename: The filename to be hashed.
        hash_func: The hash function to use (default: hashlib.sha256).

    Returns:
        A hexadecimal string representing the checksum.
    """

    if not os.path.exists(to_bytes(filename, errors='surrogate_or_strict')) or os.path.isdir(to_bytes(filename, errors='strict')):
        return None
    digest = hash_func()
    blocksize = 64 * 1024
    try:
        infile = open(to_bytes(filename, errors='surrogate_or_strict'), 'rb')
        block = infile.read(blocksize)
        while block:
            digest.update(block)
            block = infile.read(blocksize)
        infile.close()
    except IOError as e:
        raise AnsibleError(f"error while accessing the file {filename}, error was: {e}")
    return digest.hexdigest()


#
# Backwards compat functions.  Some modules include md5s in their return values
# Continue to support that for now.  As of ansible-1.8, all of those modules
# should also return "checksum" (sha1 for now)
# Do not use md5 unless it is needed for:
# 1) Optional backwards compatibility
# 2) Compliance with a third party protocol

def secure_hash_s(data, hash_func=sha1):
    # deprecated: description='Use generate_secure_checksum instead' core_version='2.21'
    # Backward compatibility
    return generate_secure_checksum(data=data, hash_func=hash_func)


def secure_hash(filename, hash_func=sha1):
    # deprecated: description='Use generate_secure_file_checksum instead' core_version='2.21'
    # Backward compatibility
    return generate_secure_file_checksum(filename=filename, hash_func=hash_func)

#
# MD5 will not work on systems which are FIPS-140-2 compliant.
#


def md5s(data):
    if not _md5:
        raise ValueError('MD5 not available.  Possibly running in FIPS mode')
    return secure_hash_s(data, _md5)


def md5(filename):
    if not _md5:
        raise ValueError('MD5 not available.  Possibly running in FIPS mode')
    return secure_hash(filename, _md5)


# The checksum algorithm must match with the algorithm in ShellModule.checksum() method
checksum = secure_hash
checksum_s = secure_hash_s

# Copyright: Contributors to the Ansible project
# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import hashlib
import os

from hashlib import sha1

try:
    from hashlib import md5 as _md5
except ImportError:
    # Assume we're running in FIPS mode here
    _md5 = None  # type: ignore[assignment]

from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils.six import string_types


def _get_available_hash_algorithms():
    """Return a dictionary of available hash function names and their associated function."""
    algorithms = {}
    for algorithm_name in hashlib.algorithms_available:
        algorithm_func = getattr(hashlib, algorithm_name, None)
        if algorithm_func:
            try:
                # Make sure the algorithm is actually available for use.
                # Not all algorithms listed as available are actually usable.
                # For example, md5 is not available in FIPS mode.
                algorithm_func()
            except Exception:
                pass
            else:
                algorithms[algorithm_name] = algorithm_func

    return algorithms


AVAILABLE_HASH_ALGORITHMS = _get_available_hash_algorithms()


def generate_secure_checksum(data, hash_func='sha256'):
    """Generates a secure checksum for the given data using the specified hash function.

    Args:
        data: The data to be hashed.
        hash_func: The hash function to use (default: sha256).

    Returns:
        A hexadecimal string representing the checksum.
    """
    if hash_func is None:
        raise ValueError("The parameter 'hash_func' can not be None")

    if isinstance(hash_func, string_types):
        if hash_func not in AVAILABLE_HASH_ALGORITHMS:
            raise ValueError(f"{hash_func} is not available. Available algorithms: {', '.join(AVAILABLE_HASH_ALGORITHMS)}")
        hash_func = getattr(hashlib, hash_func, None)

    if not callable(hash_func):
        raise ValueError("The parameter value of 'hash_func' is not callable. Please make sure hash_func is either string or method.")

    digest = hash_func()
    data = to_bytes(data, errors='surrogate_or_strict')
    digest.update(data)
    return digest.hexdigest()


def generate_secure_file_checksum(filename, hash_func='sha256', write_to=None):
    """Return a secure hash hex digest of local file, None if file is not present or a directory.

    Args:
        filename: The filename to be hashed.
        hash_func: The hash function to use (default: sha256).
        write_to: The file handle to write to (default: None).

    Returns:
        A hexadecimal string representing the checksum.
    """
    b_filename = to_bytes(filename, errors='surrogate_or_strict')

    if not os.path.exists(b_filename) or os.path.isdir(to_bytes(filename, errors='strict')):
        return None

    if hash_func is None:
        raise ValueError("The parameter 'hash_func' can not be None")

    if isinstance(hash_func, string_types):
        if hash_func not in AVAILABLE_HASH_ALGORITHMS:
            raise ValueError(f"{hash_func} is not available. Available algorithms: {', '.join(AVAILABLE_HASH_ALGORITHMS)}")
        hash_func = getattr(hashlib, hash_func, None)

    if not callable(hash_func):
        raise ValueError("The parameter value of 'hash_func' is not callable. Please make sure hash_func is either string or method.")

    digest = hash_func()
    blocksize = 64 * 1024
    try:
        infile = open(os.path.realpath(b_filename), 'rb')
        block = infile.read(blocksize)
        while block:
            if write_to is not None:
                write_to.write(block)
                write_to.flush()
            digest.update(block)
            block = infile.read(blocksize)
        infile.close()
    except IOError as e:
        raise e
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
    if not _md5:  # type: ignore[truthy-function]
        raise ValueError('MD5 not available.  Possibly running in FIPS mode')
    return secure_hash_s(data, _md5)


def md5(filename):
    if not _md5:  # type: ignore[truthy-function]
        raise ValueError('MD5 not available.  Possibly running in FIPS mode')
    return secure_hash(filename, _md5)


# The checksum algorithm must match with the algorithm in ShellModule.checksum() method
checksum = secure_hash
checksum_s = secure_hash_s

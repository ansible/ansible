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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

# Note, sha1 is the only hash algorithm compatible with python2.4 and with
# FIPS-140 mode (as of 11-2014)
try:
    from hashlib import sha1 as sha1
except ImportError:
    from sha import sha as sha1

# Backwards compat only
try:
    from hashlib import md5 as _md5
except ImportError:
    try:
        from md5 import md5 as _md5
    except ImportError:
        # Assume we're running in FIPS mode here
        _md5 = None

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes


def secure_hash_s(data, hash_func=sha1):
    ''' Return a secure hash hex digest of data. '''

    digest = hash_func()
    data = to_bytes(data, errors='surrogate_or_strict')
    digest.update(data)
    return digest.hexdigest()


def secure_hash(filename, hash_func=sha1):
    ''' Return a secure hash hex digest of local file, None if file is not present or a directory. '''

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
        raise AnsibleError("error while accessing the file %s, error was: %s" % (filename, e))
    return digest.hexdigest()

# The checksum algorithm must match with the algorithm in ShellModule.checksum() method
checksum = secure_hash
checksum_s = secure_hash_s


#
# Backwards compat functions.  Some modules include md5s in their return values
# Continue to support that for now.  As of ansible-1.8, all of those modules
# should also return "checksum" (sha1 for now)
# Do not use md5 unless it is needed for:
# 1) Optional backwards compatibility
# 2) Compliance with a third party protocol
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

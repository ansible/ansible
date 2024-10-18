# Copyright: Contributors to the Ansible project
# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

# Backward compatibility
# deprecated: description='Use ansible.module_utils.common.hashing instead' core_version='2.21'
from ansible.module_utils.common.hashing import (  # pylint: disable=unused-import
    checksum,
    checksum_s,
    generate_secure_checksum,
    generate_secure_file_checksum,
    md5, md5s, secure_hash,
    secure_hash_s,
    sha1,
    _md5,
)

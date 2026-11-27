# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from hashlib import sha1
from io import BytesIO
from unittest.mock import patch

from ansible.utils.hashing import secure_hash


def test_secure_hash_surrogate_escaped_filename():
    filename = b'/tmp/\xff'.decode('utf-8', 'surrogateescape')

    with patch('ansible.utils.hashing.os.path.exists', return_value=True), \
            patch('ansible.utils.hashing.os.path.isdir', return_value=False) as isdir, \
            patch('builtins.open', return_value=BytesIO(b'data')):
        assert secure_hash(filename) == sha1(b'data').hexdigest()

    assert isdir.call_args.args[0] == b'/tmp/\xff'

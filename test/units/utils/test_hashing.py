# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import hashlib
import io

from unittest.mock import patch

from ansible.utils.hashing import secure_hash


def test_secure_hash_filename_with_surrogate():
    with (
        patch('ansible.utils.hashing.os.path.exists', return_value=True),
        patch('ansible.utils.hashing.os.path.isdir', return_value=False),
        patch('builtins.open', return_value=io.BytesIO(b'data')),
    ):
        assert secure_hash('/nonexistent/ansible-\udcff') == hashlib.sha1(b'data').hexdigest()

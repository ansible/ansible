from __future__ import annotations

import os


class TestDirnameOrDot:
    """Ensure the dirname-or-dot pattern works for relative paths."""

    def test_relative_path_returns_dot(self):
        assert os.path.dirname(b'my_link') == b''
        assert (os.path.dirname(b'my_link') or b'.') == b'.'

    def test_absolute_path_returns_dir(self):
        assert os.path.dirname(b'/tmp/my_link') == b'/tmp'
        assert (os.path.dirname(b'/tmp/my_link') or b'.') == b'/tmp'

    def test_tmppath_relative(self):
        """Temp file for a relative path should be in current dir, not root."""
        b_path = b'my_link'
        b_dir = os.path.dirname(b_path) or b'.'
        b_tmppath = os.path.sep.encode().join(
            [b_dir, b'.12345.67890.tmp']
        )
        assert b_tmppath == b'./.12345.67890.tmp'
        assert not b_tmppath.startswith(b'/.'), "temp file must not be at filesystem root"

    def test_tmppath_absolute(self):
        b_path = b'/home/user/my_link'
        b_dir = os.path.dirname(b_path) or b'.'
        b_tmppath = os.path.sep.encode().join(
            [b_dir, b'.12345.67890.tmp']
        )
        assert b_tmppath == b'/home/user/.12345.67890.tmp'

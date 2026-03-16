from __future__ import annotations

from ansible.modules.apt_repository import SourcesList


class TestParsePreservesWhitespace:
    """Verify that _parse does not collapse significant whitespace."""

    def test_cdrom_double_space_preserved(self):
        """Spaces inside cdrom bracket notation must survive round-trip."""
        src = SourcesList.__new__(SourcesList)
        line = 'deb cdrom:[OS Astra Linux 1.8.1.6  DVD]/ 1.8_x86-64 contrib main'
        valid, enabled, source, comment = src._parse(line)
        assert valid is True
        assert enabled is True
        assert '1.8.1.6  DVD' in source, "double space inside brackets was collapsed"

    def test_normal_source_unchanged(self):
        src = SourcesList.__new__(SourcesList)
        line = 'deb http://archive.ubuntu.com/ubuntu noble main restricted'
        valid, enabled, source, comment = src._parse(line)
        assert valid is True
        assert source == 'deb http://archive.ubuntu.com/ubuntu noble main restricted'

    def test_disabled_source(self):
        src = SourcesList.__new__(SourcesList)
        line = '# deb http://archive.ubuntu.com/ubuntu noble main'
        valid, enabled, source, comment = src._parse(line)
        assert valid is True
        assert enabled is False

    def test_source_with_comment(self):
        src = SourcesList.__new__(SourcesList)
        line = 'deb http://example.com/repo stable main # my repo'
        valid, enabled, source, comment = src._parse(line)
        assert valid is True
        assert comment == 'my repo'
        assert source == 'deb http://example.com/repo stable main'

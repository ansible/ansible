from __future__ import annotations

from ansible.modules.apt_repository import UbuntuSourcesList


class TestUbuntuCodename:
    """Test _ubuntu_codename() reads UBUNTU_CODENAME from os-release."""

    def _write_os_release(self, tmp_path, content):
        p = tmp_path / "os-release"
        p.write_text(content)
        return str(p)

    def test_derivative_returns_ubuntu_codename(self, tmp_path, monkeypatch):
        path = self._write_os_release(tmp_path, (
            'ID=linuxmint\n'
            'VERSION_CODENAME=zara\n'
            'UBUNTU_CODENAME=noble\n'
        ))
        monkeypatch.setattr(UbuntuSourcesList, '_OS_RELEASE_PATHS', (path,))
        assert UbuntuSourcesList._ubuntu_codename() == 'noble'

    def test_plain_ubuntu(self, tmp_path, monkeypatch):
        path = self._write_os_release(tmp_path, (
            'ID=ubuntu\n'
            'VERSION_CODENAME=noble\n'
            'UBUNTU_CODENAME=noble\n'
        ))
        monkeypatch.setattr(UbuntuSourcesList, '_OS_RELEASE_PATHS', (path,))
        assert UbuntuSourcesList._ubuntu_codename() == 'noble'

    def test_debian_returns_none(self, tmp_path, monkeypatch):
        path = self._write_os_release(tmp_path, (
            'ID=debian\n'
            'VERSION_CODENAME=bookworm\n'
        ))
        monkeypatch.setattr(UbuntuSourcesList, '_OS_RELEASE_PATHS', (path,))
        assert UbuntuSourcesList._ubuntu_codename() is None

    def test_missing_file_returns_none(self, monkeypatch):
        monkeypatch.setattr(UbuntuSourcesList, '_OS_RELEASE_PATHS', ('/nonexistent/path',))
        assert UbuntuSourcesList._ubuntu_codename() is None

    def test_empty_value_skipped(self, tmp_path, monkeypatch):
        path = self._write_os_release(tmp_path, (
            'UBUNTU_CODENAME=\n'
        ))
        monkeypatch.setattr(UbuntuSourcesList, '_OS_RELEASE_PATHS', (path,))
        assert UbuntuSourcesList._ubuntu_codename() is None

    def test_quoted_value(self, tmp_path, monkeypatch):
        path = self._write_os_release(tmp_path, (
            'UBUNTU_CODENAME="noble"\n'
        ))
        monkeypatch.setattr(UbuntuSourcesList, '_OS_RELEASE_PATHS', (path,))
        assert UbuntuSourcesList._ubuntu_codename() == 'noble'

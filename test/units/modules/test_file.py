# Copyright: (c) 2026, ZXLyyds100
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import errno
import json
import os
from pathlib import Path

import pytest

from ansible.module_utils.testing import patch_module_args
from ansible.modules import file as file_module


pytestmark = pytest.mark.usefixtures('module_env_mocker')


@pytest.mark.parametrize('trailing_slash', (False, True))
def test_absent_directory_removed_concurrently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], trailing_slash: bool,
) -> None:
    directory = tmp_path / 'directory'
    directory.mkdir()
    (directory / 'file').write_text('content')
    path = str(directory) + ('/' if trailing_slash else '')
    real_rmtree = file_module.shutil.rmtree

    def remove_concurrently(path: bytes, ignore_errors: bool = False) -> None:
        if Path(os.fsdecode(path)) != directory:
            return real_rmtree(path, ignore_errors=ignore_errors)
        real_rmtree(path)
        real_rmtree(path, ignore_errors=ignore_errors)

    monkeypatch.setattr(file_module.shutil, 'rmtree', remove_concurrently)

    with patch_module_args({'path': path, 'state': 'absent'}):
        with pytest.raises(SystemExit) as exc:
            file_module.main()

    result = json.loads(capsys.readouterr().out)
    assert exc.value.code == 0
    assert result['state'] == 'absent'
    assert result['changed'] is True
    assert not directory.exists()


def test_absent_missing_child_does_not_hide_remaining_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    directory = tmp_path / 'directory'
    directory.mkdir()
    child = directory / 'child'
    child.mkdir()
    sentinel = directory / 'sentinel'
    sentinel.write_text('keep')
    real_rmtree = file_module.shutil.rmtree

    def remove_child_concurrently(path: bytes, ignore_errors: bool = False) -> None:
        if Path(os.fsdecode(path)) != directory:
            return real_rmtree(path, ignore_errors=ignore_errors)
        real_rmtree(child)
        raise FileNotFoundError(errno.ENOENT, 'Child disappeared', str(child))

    monkeypatch.setattr(file_module.shutil, 'rmtree', remove_child_concurrently)

    with patch_module_args({'path': str(directory), 'state': 'absent'}):
        with pytest.raises(SystemExit) as exc:
            file_module.main()

    result = json.loads(capsys.readouterr().out)
    assert exc.value.code == 1
    assert result['failed'] is True
    assert 'rmtree failed' in result['msg']
    assert sentinel.read_text() == 'keep'


@pytest.mark.parametrize('trailing_slash', (False, True))
@pytest.mark.parametrize('replacement', ('file', 'dangling_link'))
def test_absent_replaced_directory_still_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], trailing_slash: bool, replacement: str,
) -> None:
    directory = tmp_path / 'directory'
    directory.mkdir()
    path = str(directory) + ('/' if trailing_slash else '')
    real_rmtree = file_module.shutil.rmtree

    def replace_concurrently(path: bytes, ignore_errors: bool = False) -> None:
        if Path(os.fsdecode(path)) != directory:
            return real_rmtree(path, ignore_errors=ignore_errors)
        real_rmtree(path)
        try:
            real_rmtree(path, ignore_errors=ignore_errors)
        except FileNotFoundError:
            if replacement == 'file':
                directory.write_text('keep')
            else:
                directory.symlink_to(tmp_path / 'missing')
            raise

    monkeypatch.setattr(file_module.shutil, 'rmtree', replace_concurrently)

    with patch_module_args({'path': path, 'state': 'absent'}):
        with pytest.raises(SystemExit) as exc:
            file_module.main()

    result = json.loads(capsys.readouterr().out)
    assert exc.value.code == 1
    assert result['failed'] is True
    assert 'rmtree failed' in result['msg']
    if replacement == 'file':
        assert directory.read_text() == 'keep'
    else:
        assert directory.is_symlink()
        assert not directory.exists()


@pytest.mark.parametrize('error_number', (errno.EACCES, errno.ENOTEMPTY))
def test_absent_other_removal_errors_still_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], error_number: int,
) -> None:
    directory = tmp_path / 'directory'
    directory.mkdir()
    sentinel = directory / 'sentinel'
    sentinel.write_text('keep')
    real_rmtree = file_module.shutil.rmtree

    def fail_removal(path: bytes, ignore_errors: bool = False) -> None:
        if Path(os.fsdecode(path)) != directory:
            return real_rmtree(path, ignore_errors=ignore_errors)
        raise OSError(error_number, 'Removal failed', path)

    monkeypatch.setattr(file_module.shutil, 'rmtree', fail_removal)

    with patch_module_args({'path': str(directory), 'state': 'absent'}):
        with pytest.raises(SystemExit) as exc:
            file_module.main()

    result = json.loads(capsys.readouterr().out)
    assert exc.value.code == 1
    assert result['failed'] is True
    assert 'rmtree failed' in result['msg']
    assert sentinel.read_text() == 'keep'


@pytest.mark.parametrize('check_mode', (False, True))
def test_absent_directory_normal_removal_and_check_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], check_mode: bool,
) -> None:
    directory = tmp_path / 'directory'
    directory.mkdir()
    (directory / 'file').write_text('content')

    with patch_module_args({'path': str(directory), 'state': 'absent', '_ansible_check_mode': check_mode}):
        with pytest.raises(SystemExit) as exc:
            file_module.main()

    result = json.loads(capsys.readouterr().out)
    assert exc.value.code == 0
    assert result['state'] == ('directory' if check_mode else 'absent')
    assert result['changed'] is True
    assert directory.exists() is check_mode


def test_absent_directory_already_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with patch_module_args({'path': str(tmp_path / 'absent'), 'state': 'absent'}):
        with pytest.raises(SystemExit) as exc:
            file_module.main()

    result = json.loads(capsys.readouterr().out)
    assert exc.value.code == 0
    assert result['state'] == 'absent'
    assert result['changed'] is False

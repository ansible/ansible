# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import errno
import json
from itertools import product

import pytest

from ansible.module_utils import basic


@pytest.fixture
def atomic_am(am, mocker):
    am.selinux_enabled = mocker.MagicMock()
    am.selinux_context = mocker.MagicMock()
    am.selinux_default_context = mocker.MagicMock()
    am.set_context_if_different = mocker.MagicMock()

    yield am


@pytest.fixture
def atomic_mocks(mocker, monkeypatch):
    environ = dict()
    mocks = {
        'chmod': mocker.patch('os.chmod'),
        'chown': mocker.patch('os.chown'),
        'close': mocker.patch('os.close'),
        'environ': mocker.patch('os.environ', environ),
        'getlogin': mocker.patch('os.getlogin'),
        'getuid': mocker.patch('os.getuid'),
        'path_exists': mocker.patch('os.path.exists'),
        'rename': mocker.patch('os.rename'),
        'stat': mocker.patch('os.stat'),
        'umask': mocker.patch('os.umask'),
        'getpwuid': mocker.patch('pwd.getpwuid'),
        'copy2': mocker.patch('shutil.copy2'),
        'copyfileobj': mocker.patch('shutil.copyfileobj'),
        'move': mocker.patch('shutil.move'),
        'mkstemp': mocker.patch('tempfile.mkstemp'),
    }

    mocks['getlogin'].return_value = 'root'
    mocks['getuid'].return_value = 0
    mocks['getpwuid'].return_value = ('root', '', 0, 0, '', '', '')
    mocks['umask'].side_effect = [18, 0]
    mocks['rename'].return_value = None

    # normalize OS specific features
    monkeypatch.delattr(os, 'chflags', raising=False)

    yield mocks


@pytest.fixture
def fake_stat(mocker):
    stat1 = mocker.MagicMock()
    stat1.st_mode = 0o0644
    stat1.st_uid = 0
    stat1.st_gid = 0
    stat1.st_flags = 0
    yield stat1


@pytest.mark.parametrize('stdin, selinux', product([{}], (True, False)), indirect=['stdin'])
def test_new_file(atomic_am, atomic_mocks, mocker, selinux):
    # test destination does not exist, login name = 'root', no environment, os.rename() succeeds
    mock_context = atomic_am.selinux_default_context.return_value
    atomic_mocks['path_exists'].return_value = False
    atomic_am.selinux_enabled.return_value = selinux

    atomic_am.atomic_move('/path/to/src', '/path/to/dest')

    atomic_mocks['rename'].assert_called_with(b'/path/to/src', b'/path/to/dest')
    assert atomic_mocks['chmod'].call_args_list == [mocker.call(b'/path/to/dest', basic.DEFAULT_PERM & ~18)]

    if selinux:
        assert atomic_am.selinux_default_context.call_args_list == [mocker.call('/path/to/dest')]
        assert atomic_am.set_context_if_different.call_args_list == [mocker.call('/path/to/dest', mock_context, False)]
    else:
        assert not atomic_am.selinux_default_context.called
        assert not atomic_am.set_context_if_different.called


@pytest.mark.parametrize('stdin, selinux', product([{}], (True, False)), indirect=['stdin'])
def test_existing_file(atomic_am, atomic_mocks, fake_stat, mocker, selinux):
    # Test destination already present
    mock_context = atomic_am.selinux_context.return_value
    atomic_mocks['stat'].return_value = fake_stat
    atomic_mocks['path_exists'].return_value = True
    atomic_am.selinux_enabled.return_value = selinux

    atomic_am.atomic_move('/path/to/src', '/path/to/dest')

    atomic_mocks['rename'].assert_called_with(b'/path/to/src', b'/path/to/dest')
    assert atomic_mocks['chmod'].call_args_list == [mocker.call(b'/path/to/src', basic.DEFAULT_PERM & ~18)]

    if selinux:
        assert atomic_am.set_context_if_different.call_args_list == [mocker.call('/path/to/dest', mock_context, False)]
        assert atomic_am.selinux_context.call_args_list == [mocker.call('/path/to/dest')]
    else:
        assert not atomic_am.selinux_default_context.called
        assert not atomic_am.set_context_if_different.called


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_no_tty_fallback(atomic_am, atomic_mocks, fake_stat, mocker):
    """Raise OSError when using getlogin() to simulate no tty cornercase"""
    mock_context = atomic_am.selinux_context.return_value
    atomic_mocks['stat'].return_value = fake_stat
    atomic_mocks['path_exists'].return_value = True
    atomic_am.selinux_enabled.return_value = True
    atomic_mocks['getlogin'].side_effect = OSError()
    atomic_mocks['environ']['LOGNAME'] = 'root'

    atomic_am.atomic_move('/path/to/src', '/path/to/dest')

    atomic_mocks['rename'].assert_called_with(b'/path/to/src', b'/path/to/dest')
    assert atomic_mocks['chmod'].call_args_list == [mocker.call(b'/path/to/src', basic.DEFAULT_PERM & ~18)]

    assert atomic_am.set_context_if_different.call_args_list == [mocker.call('/path/to/dest', mock_context, False)]
    assert atomic_am.selinux_context.call_args_list == [mocker.call('/path/to/dest')]


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_existing_file_stat_failure(atomic_am, atomic_mocks, mocker):
    """Failure to stat an existing file in order to copy permissions propogates the error (unless EPERM)"""
    atomic_mocks['stat'].side_effect = OSError()
    atomic_mocks['path_exists'].return_value = True

    with pytest.raises(OSError):
        atomic_am.atomic_move('/path/to/src', '/path/to/dest')


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_existing_file_stat_perms_failure(atomic_am, atomic_mocks, mocker):
    """Failure to stat an existing file to copy the permissions due to permissions passes fine"""
    # and now have os.stat return EPERM, which should not fail
    mock_context = atomic_am.selinux_context.return_value
    atomic_mocks['stat'].side_effect = OSError(errno.EPERM, 'testing os stat with EPERM')
    atomic_mocks['path_exists'].return_value = True
    atomic_am.selinux_enabled.return_value = True

    atomic_am.atomic_move('/path/to/src', '/path/to/dest')

    atomic_mocks['rename'].assert_called_with(b'/path/to/src', b'/path/to/dest')
    # FIXME: Should atomic_move() set a default permission value when it cannot retrieve the
    # existing file's permissions?  (Right now it's up to the calling code.
    # assert atomic_mocks['chmod'].call_args_list == [mocker.call(b'/path/to/src', basic.DEFAULT_PERM & ~18)]
    assert atomic_am.set_context_if_different.call_args_list == [mocker.call('/path/to/dest', mock_context, False)]
    assert atomic_am.selinux_context.call_args_list == [mocker.call('/path/to/dest')]


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_rename_failure(atomic_am, atomic_mocks, mocker, capfd):
    """Test os.rename fails with EIO, causing it to bail out"""
    atomic_mocks['path_exists'].side_effect = [False, False]
    atomic_mocks['rename'].side_effect = OSError(errno.EIO, 'failing with EIO')

    with pytest.raises(SystemExit):
        atomic_am.atomic_move('/path/to/src', '/path/to/dest')

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert 'Could not replace file' in results['msg']
    assert 'failing with EIO' in results['msg']
    assert results['failed']


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_rename_perms_fail_temp_creation_fails(atomic_am, atomic_mocks, mocker, capfd):
    """Test os.rename fails with EPERM working but failure in mkstemp"""
    atomic_mocks['path_exists'].return_value = False
    atomic_mocks['close'].return_value = None
    atomic_mocks['rename'].side_effect = [OSError(errno.EPERM, 'failing with EPERM'), None]
    atomic_mocks['mkstemp'].return_value = None
    atomic_mocks['mkstemp'].side_effect = OSError()
    atomic_am.selinux_enabled.return_value = False

    with pytest.raises(SystemExit):
        atomic_am.atomic_move('/path/to/src', '/path/to/dest')

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert 'is not writable by the current user' in results['msg']
    assert results['failed']


@pytest.mark.parametrize('stdin, selinux', product([{}], (True, False)), indirect=['stdin'])
def test_rename_perms_fail_temp_succeeds(atomic_am, atomic_mocks, fake_stat, mocker, selinux):
    """Test os.rename raising an error but fallback to using mkstemp works"""
    mock_context = atomic_am.selinux_default_context.return_value
    atomic_mocks['path_exists'].return_value = False
    atomic_mocks['rename'].side_effect = [OSError(errno.EPERM, 'failing with EPERM'), None]
    atomic_mocks['stat'].return_value = fake_stat
    atomic_mocks['stat'].side_effect = None
    atomic_mocks['mkstemp'].return_value = (None, '/path/to/tempfile')
    atomic_mocks['mkstemp'].side_effect = None
    atomic_am.selinux_enabled.return_value = selinux

    atomic_am.atomic_move('/path/to/src', '/path/to/dest')
    assert atomic_mocks['rename'].call_args_list == [mocker.call(b'/path/to/src', b'/path/to/dest'),
                                                     mocker.call(b'/path/to/tempfile', b'/path/to/dest')]
    assert atomic_mocks['chmod'].call_args_list == [mocker.call(b'/path/to/dest', basic.DEFAULT_PERM & ~18)]

    if selinux:
        assert atomic_am.selinux_default_context.call_args_list == [mocker.call('/path/to/dest')]
        assert atomic_am.set_context_if_different.call_args_list == [mocker.call(b'/path/to/tempfile', mock_context, False),
                                                                     mocker.call('/path/to/dest', mock_context, False)]
    else:
        assert not atomic_am.selinux_default_context.called
        assert not atomic_am.set_context_if_different.called

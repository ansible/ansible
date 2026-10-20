# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from unittest.mock import MagicMock

from ansible.modules import user as user_module

HASH = '$6$saltsalt$' + 'a' * 86
OLD_HASH = '$6$oldsalt$' + 'b' * 86
NAME = 'zz71209'

DEFAULT_PARAMS = dict(
    state='present',
    name=NAME,
    uid=None,
    hidden=None,
    non_unique=False,
    seuser=None,
    group=None,
    groups=None,
    comment=None,
    shell=None,
    password=None,
    force=False,
    remove=False,
    create_home=True,
    move_home=False,
    skeleton=None,
    system=False,
    login_class=None,
    append=False,
    generate_ssh_key=None,
    ssh_key_bits=0,
    ssh_key_type='rsa',
    ssh_key_comment='',
    ssh_key_passphrase=None,
    ssh_key_file=None,
    update_password='always',
    home=None,
    expires=None,
    password_lock=None,
    local=None,
    profile=None,
    authorization=None,
    role=None,
    password_expire_max=None,
    password_expire_min=None,
    password_expire_warn=None,
    umask=None,
    password_expire_account_disable=None,
    uid_min=None,
    uid_max=None,
)


def _make_user(mocker, missing=(), check_mode=False, current_password=OLD_HASH, **params):
    module = MagicMock()
    module.params = dict(DEFAULT_PARAMS, **params)
    module.check_mode = check_mode
    module.selinux_enabled.return_value = False

    def get_bin_path(name, required=False, opt_dirs=None):
        if name in missing:
            if required:
                raise AssertionError('required binary %s is missing' % name)
            return None
        return '/usr/sbin/%s' % name

    module.get_bin_path.side_effect = get_bin_path
    module.run_command.return_value = (0, '', '')

    # Always use the generic (shadow-utils) implementation regardless of the test host.
    mocker.patch.object(user_module, 'get_platform_subclass', return_value=user_module.User)
    mocker.patch.object(user_module.User, 'group_exists', return_value=False)
    mocker.patch.object(user_module.User, '_check_usermod_append', return_value=True)
    mocker.patch.object(user_module.User, 'user_info',
                        return_value=(NAME, current_password, 1000, 1000, '', '/home/%s' % NAME, '/bin/sh'))
    return user_module.User(module)


def _calls(user):
    """Return a list of (argv, data) for every command run by the module."""
    result = []
    for call in user.module.run_command.call_args_list:
        result.append((list(call.args[0]), call.kwargs.get('data')))
    return result


def _assert_hash_not_in_argv(user, secret=HASH):
    for argv, dummy in _calls(user):
        for arg in argv:
            assert secret not in arg, 'password hash leaked into argv: %r' % (argv,)
        assert '-p' not in argv, 'unexpected -p in argv: %r' % (argv,)


def _chpasswd_calls(user):
    return [(argv, data) for argv, data in _calls(user) if argv[0].endswith('/chpasswd')]


@pytest.mark.parametrize('password_lock, expected', [
    (None, HASH),
    (False, HASH),
    (True, '!' + HASH),
], ids=['lock_none', 'lock_false', 'lock_true'])
def test_create_user_password_via_stdin(mocker, password_lock, expected):
    user = _make_user(mocker, password=HASH, password_lock=password_lock)

    rc, out, err = user.create_user()

    assert rc == 0
    _assert_hash_not_in_argv(user)
    calls = _calls(user)
    assert calls[0][0][0] == '/usr/sbin/useradd'
    assert calls[0][0][-1] == NAME
    assert _chpasswd_calls(user) == [(['/usr/sbin/chpasswd', '-e'], '%s:%s' % (NAME, expected))]


def test_create_user_without_password_does_not_run_chpasswd(mocker):
    user = _make_user(mocker, password_lock=True)

    rc, out, err = user.create_user()

    assert rc == 0
    assert _chpasswd_calls(user) == []
    assert len(_calls(user)) == 1


def test_create_user_useradd_failure_skips_chpasswd(mocker):
    user = _make_user(mocker, password=HASH)
    user.module.run_command.return_value = (9, '', 'useradd: user already exists')

    rc, out, err = user.create_user()

    assert rc == 9
    assert _chpasswd_calls(user) == []


def test_create_user_chpasswd_failure_is_reported(mocker):
    user = _make_user(mocker, password=HASH)
    user.module.run_command.side_effect = [(0, '', ''), (1, '', 'chpasswd: error')]

    rc, out, err = user.create_user()

    assert rc == 1
    assert 'chpasswd: error' in err


@pytest.mark.parametrize('password_lock, current, expected', [
    (None, OLD_HASH, HASH),
    (None, '!' + OLD_HASH, HASH),
    (False, OLD_HASH, HASH),
    (False, '!' + OLD_HASH, HASH),
    (True, OLD_HASH, '!' + HASH),
    (True, '!' + OLD_HASH, '!' + HASH),
], ids=['lock_none-unlocked', 'lock_none-locked', 'lock_false-unlocked', 'lock_false-locked', 'lock_true-unlocked', 'lock_true-locked'])
def test_modify_user_password_via_stdin(mocker, password_lock, current, expected):
    user = _make_user(mocker, password=HASH, password_lock=password_lock, current_password=current)

    rc, out, err = user.modify_user()

    assert rc == 0
    _assert_hash_not_in_argv(user)
    # -L/-U are mutually exclusive with setting the hash, the lock is carried by the '!' prefix
    for argv, dummy in _calls(user):
        assert '-L' not in argv and '-U' not in argv
    assert _chpasswd_calls(user) == [(['/usr/sbin/chpasswd', '-e'], '%s:%s' % (NAME, expected))]
    # nothing else to change, so usermod itself is not run
    assert len(_calls(user)) == 1


def test_modify_user_other_changes_and_password(mocker):
    user = _make_user(mocker, password=HASH, shell='/bin/bash', password_lock=True)

    rc, out, err = user.modify_user()

    assert rc == 0
    _assert_hash_not_in_argv(user)
    calls = _calls(user)
    assert calls[0] == (['/usr/sbin/usermod', '-s', '/bin/bash', NAME], None)
    assert calls[1] == (['/usr/sbin/chpasswd', '-e'], '%s:!%s' % (NAME, HASH))


def test_modify_user_usermod_failure_skips_chpasswd(mocker):
    user = _make_user(mocker, password=HASH, shell='/bin/bash')
    user.module.run_command.return_value = (6, '', 'usermod: error')

    rc, out, err = user.modify_user()

    assert rc == 6
    assert _chpasswd_calls(user) == []


@pytest.mark.parametrize('password_lock, current, expected_argv', [
    # same hash, only the lock state changes: unchanged behaviour (usermod -L / -U, no hash involved)
    (True, HASH, ['/usr/sbin/usermod', '-L', NAME]),
    (False, '!' + HASH, ['/usr/sbin/usermod', '-U', NAME]),
], ids=['lock', 'unlock'])
def test_modify_user_lock_only(mocker, password_lock, current, expected_argv):
    user = _make_user(mocker, password=HASH, password_lock=password_lock, current_password=current)

    rc, out, err = user.modify_user()

    assert rc == 0
    assert _calls(user) == [(expected_argv, None)]


@pytest.mark.parametrize('password_lock, current', [
    (None, HASH),
    (None, '!' + HASH),
    (True, '!' + HASH),
    (False, HASH),
], ids=['lock_none-unlocked', 'lock_none-locked', 'lock_true-locked', 'lock_false-unlocked'])
def test_modify_user_password_unchanged(mocker, password_lock, current):
    user = _make_user(mocker, password=HASH, password_lock=password_lock, current_password=current)

    rc, out, err = user.modify_user()

    assert rc is None
    assert _calls(user) == []


def test_modify_user_update_password_on_create(mocker):
    user = _make_user(mocker, password=HASH, update_password='on_create')

    rc, out, err = user.modify_user()

    assert rc is None
    assert _calls(user) == []


def test_modify_user_check_mode(mocker):
    user = _make_user(mocker, password=HASH, check_mode=True)

    rc, out, err = user.modify_user()

    assert rc == 0
    assert _calls(user) == []


def test_chpasswd_missing_falls_back_to_argv(mocker):
    user = _make_user(mocker, missing=('chpasswd',), password=HASH, password_lock=True)

    rc, out, err = user.create_user()

    assert rc == 0
    assert user.module.warn.called
    argv = _calls(user)[0][0]
    assert argv[argv.index('-p') + 1] == '!' + HASH


@pytest.mark.parametrize('password', [HASH + '\nroot:', 'a:b'], ids=['newline', 'colon'])
def test_password_with_line_or_field_separator_is_not_sent_to_chpasswd(mocker, password):
    user = _make_user(mocker, password=password)

    user.modify_user()

    # never feed a value to chpasswd that could inject a second line or field,
    # keep the previous behaviour (usermod validates and rejects the value)
    assert _chpasswd_calls(user) == []
    argv = _calls(user)[0][0]
    assert argv[argv.index('-p') + 1] == password


def test_local_keeps_libuser_behaviour(mocker):
    user = _make_user(mocker, password=HASH, local=True)

    user.create_user()

    assert _chpasswd_calls(user) == []
    argv = _calls(user)[0][0]
    assert argv[0] == '/usr/sbin/luseradd'
    assert argv[argv.index('-p') + 1] == HASH

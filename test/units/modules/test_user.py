# Copyright (c) 2026 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

from unittest.mock import MagicMock, patch
from collections import defaultdict, namedtuple

from ansible.modules import user


SpwdStruct = namedtuple('spwd', ['sp_nam', 'sp_pwdp', 'sp_lstchg', 'sp_min', 'sp_max', 'sp_warn', 'sp_inact', 'sp_expire', 'sp_flag'])


def get_default_params(overrides=None):
    params = defaultdict(lambda: None, {
        'name': 'testuser',
        'state': 'present',
        'non_unique': False,
        'force': False,
        'remove': False,
        'create_home': True,
        'move_home': False,
        'system': False,
        'append': False,
        'local': False,
        'update_password': 'always',
    })
    if overrides:
        params.update(overrides)
    return params


def test_set_password_expire_last_change_day():
    module = MagicMock()
    module.params = get_default_params({'password_last_change_day': 0})
    module.get_bin_path.return_value = '/usr/bin/chage'

    with patch('platform.system', return_value='Linux'):
        u = user.User(module)
    u.execute_command = MagicMock(return_value=(0, '', ''))

    # Mock shadow info where sp_lstchg is currently 19000 (different from 0)
    fake_spwd = SpwdStruct(
        sp_nam='testuser',
        sp_pwdp='*',
        sp_lstchg=19000,
        sp_min=0,
        sp_max=99999,
        sp_warn=7,
        sp_inact=-1,
        sp_expire=-1,
        sp_flag=0,
    )

    with patch.object(user, 'HAVE_SPWD', True), patch.object(user, 'getspnam', return_value=fake_spwd):
        rc, out, err = u.set_password_expire()

    assert rc == 0
    u.execute_command.assert_called_once_with(['/usr/bin/chage', '-d', '0', 'testuser'])


def test_set_password_expire_no_change_needed():
    module = MagicMock()
    module.params = get_default_params({'password_last_change_day': 19000})

    with patch('platform.system', return_value='Linux'):
        u = user.User(module)
    u.execute_command = MagicMock()

    # Mock shadow info where sp_lstchg already matches 19000
    fake_spwd = SpwdStruct(
        sp_nam='testuser',
        sp_pwdp='*',
        sp_lstchg=19000,
        sp_min=0,
        sp_max=99999,
        sp_warn=7,
        sp_inact=-1,
        sp_expire=-1,
        sp_flag=0,
    )

    with patch.object(user, 'HAVE_SPWD', True), patch.object(user, 'getspnam', return_value=fake_spwd):
        rc, out, err = u.set_password_expire()

    assert rc is None
    assert u.execute_command.call_count == 0

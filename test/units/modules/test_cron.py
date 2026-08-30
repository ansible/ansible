# Copyright (c) 2026 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ansible.modules import cron


def test_cron_env_with_cron_file_does_not_require_user(set_module_args, capfd):
    """Verify that adding an environment variable with cron_file does not require user."""
    set_module_args({
        'name': 'PATH',
        'job': '/usr/local/bin:$PATH',
        'state': 'present',
        'cron_file': 'ansible-pull',
        'env': True,
    })

    fake_crontab = MagicMock()
    fake_crontab.cron_file = '/etc/cron.d/ansible-pull'
    fake_crontab.find_env.return_value = []
    fake_crontab.n_existing = ''
    fake_crontab.get_jobnames.return_value = []
    fake_crontab.get_envnames.return_value = ['PATH']

    with patch.object(cron, 'CronTab', return_value=fake_crontab):
        with pytest.raises(SystemExit) as exc:
            cron.main()

    assert exc.value.code == 0
    out, err = capfd.readouterr()
    res = json.loads(out)
    assert res['changed'] is True
    fake_crontab.add_env.assert_called_once_with('PATH="/usr/local/bin:$PATH"', None, None)
    fake_crontab.write.assert_called_once()


def test_cron_job_with_cron_file_requires_user(set_module_args, capfd):
    """Verify that adding a normal cron job with cron_file still requires user."""
    set_module_args({
        'name': 'check job',
        'job': 'ls -la',
        'state': 'present',
        'cron_file': 'my-cron',
        'env': False,
    })

    fake_crontab = MagicMock()

    with patch.object(cron, 'CronTab', return_value=fake_crontab):
        with pytest.raises(SystemExit) as exc:
            cron.main()

    assert exc.value.code != 0
    out, err = capfd.readouterr()
    res = json.loads(out)
    assert res['failed'] is True
    assert "To use cron_file=... parameter you must specify user=... as well" in res['msg']

# -*- coding: utf-8 -*-
# Copyright:
#   (c) 2025 Ansible Project
# License: GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import stat
import unittest.mock

from ansible.modules.cron import CronTab


def test_write_tempfile_is_not_group_or_world_writable() -> None:
    """The temporary crontab staged for ``crontab <file>`` must not be writable
    by group or other, otherwise a local user could tamper with its contents
    before it is installed (often as root)."""
    module = unittest.mock.MagicMock()
    module.get_bin_path.return_value = '/usr/bin/crontab'

    observed = {}

    def run_command(cmd, **kwargs):
        # The install command is "<crontab> <path>"; capture the staged file's
        # mode exactly when crontab would read it.
        candidate = cmd.split()[-1]
        if os.path.isfile(candidate):
            observed['mode'] = stat.S_IMODE(os.stat(candidate).st_mode)
        return (0, '', '')

    module.run_command.side_effect = run_command

    crontab = CronTab(module)
    crontab.write()

    assert 'mode' in observed
    assert not observed['mode'] & stat.S_IWGRP
    assert not observed['mode'] & stat.S_IWOTH

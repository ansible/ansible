# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import os
import shutil
import tempfile

import pytest

from ansible.compat.tests.mock import patch


class TestAnsibleModuleTmpDir:

    DATA = (
        (
            {
                "_ansible_tmpdir": "/path/to/dir",
                "_ansible_remote_tmp": "/path/tmpdir",
                "_ansible_keep_remote_files": False,
            },
            True,
            "/path/to/dir"
        ),
        (
            {
                "_ansible_tmpdir": None,
                "_ansible_remote_tmp": "/path/tmpdir",
                "_ansible_keep_remote_files": False
            },
            False,
            "/path/tmpdir/ansible-moduletmp-42-"
        ),
        (
            {
                "_ansible_tmpdir": None,
                "_ansible_remote_tmp": "/path/tmpdir",
                "_ansible_keep_remote_files": False
            },
            True,
            "/path/tmpdir/ansible-moduletmp-42-"
        ),
        (
            {
                "_ansible_tmpdir": None,
                "_ansible_remote_tmp": "$HOME/.test",
                "_ansible_keep_remote_files": False
            },
            False,
            os.path.join(os.environ['HOME'], ".test/ansible-moduletmp-42-")
        ),
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('stdin, expected, stat_exists', ((s, e, t) for s, t, e in DATA),
                             indirect=['stdin'])
    def test_tmpdir_property(self, am, monkeypatch, expected, stat_exists):
        makedirs = {'called': False}

        def mock_mkdtemp(prefix, dir):
            return os.path.join(dir, prefix)

        def mock_makedirs(path, mode):
            makedirs['called'] = True
            expected = os.path.expanduser(os.path.expandvars(am._remote_tmp))
            assert path == expected
            assert mode == 0o700
            return

        monkeypatch.setattr(tempfile, 'mkdtemp', mock_mkdtemp)
        monkeypatch.setattr(os.path, 'exists', lambda x: stat_exists)
        monkeypatch.setattr(os, 'makedirs', mock_makedirs)
        monkeypatch.setattr(shutil, 'rmtree', lambda x: None)

        with patch('time.time', return_value=42):
            actual_tmpdir = am.tmpdir
        assert actual_tmpdir == expected

        # verify subsequent calls always produces the same tmpdir
        assert am.tmpdir == actual_tmpdir

        if not stat_exists:
            assert makedirs['called']

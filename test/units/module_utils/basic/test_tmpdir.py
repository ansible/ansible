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
            "/path/to/dir"
        ),
        (
            {
                "_ansible_tmpdir": None,
                "_ansible_remote_tmp": "/path/tmpdir",
                "_ansible_keep_remote_files": False
            },
            "/path/tmpdir/ansible-moduletmp-42-"
        ),
        (
            {
                "_ansible_tmpdir": None,
                "_ansible_remote_tmp": "$HOME/.test",
                "_ansible_keep_remote_files": False
            },
            os.path.join(os.environ['HOME'], ".test/ansible-moduletmp-42-")
        ),
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('stdin, expected', ((s, e) for s, e in DATA),
                             indirect=['stdin'])
    def test_tmpdir_property(self, am, monkeypatch, expected):
        def mock_mkdtemp(prefix, dir):
            return os.path.join(dir, prefix)
        monkeypatch.setattr(tempfile, 'mkdtemp', mock_mkdtemp)
        monkeypatch.setattr(shutil, 'rmtree', lambda x: None)

        with patch('time.time', return_value=42):
            actual_tmpdir = am.tmpdir
        assert actual_tmpdir == expected

        # verify subsequent calls always produces the same tmpdir
        assert am.tmpdir == actual_tmpdir

# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import shutil
import tempfile

import pytest

from units.compat.mock import patch, MagicMock
from ansible.module_utils._text import to_bytes

from ansible.module_utils import basic


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
    @pytest.mark.parametrize('args, expected, stat_exists', ((s, e, t) for s, t, e in DATA))
    def test_tmpdir_property(self, monkeypatch, args, expected, stat_exists):
        makedirs = {'called': False}

        def mock_mkdtemp(prefix, dir):
            return os.path.join(dir, prefix)

        def mock_makedirs(path, mode):
            makedirs['called'] = True
            makedirs['path'] = path
            makedirs['mode'] = mode
            return

        monkeypatch.setattr(tempfile, 'mkdtemp', mock_mkdtemp)
        monkeypatch.setattr(os.path, 'exists', lambda x: stat_exists)
        monkeypatch.setattr(os, 'makedirs', mock_makedirs)
        monkeypatch.setattr(shutil, 'rmtree', lambda x: None)
        monkeypatch.setattr(basic, '_ANSIBLE_ARGS', to_bytes(json.dumps({'ANSIBLE_MODULE_ARGS': args})))

        with patch('time.time', return_value=42):
            am = basic.AnsibleModule(argument_spec={})
            actual_tmpdir = am.tmpdir

        assert actual_tmpdir == expected

        # verify subsequent calls always produces the same tmpdir
        assert am.tmpdir == actual_tmpdir

        if not stat_exists:
            assert makedirs['called']
            expected = os.path.expanduser(os.path.expandvars(am._remote_tmp))
            assert makedirs['path'] == expected
            assert makedirs['mode'] == 0o700

    @pytest.mark.parametrize('stdin', ({"_ansible_tmpdir": None,
                                        "_ansible_remote_tmp": "$HOME/.test",
                                        "_ansible_keep_remote_files": True},),
                             indirect=['stdin'])
    def test_tmpdir_makedirs_failure(self, am, monkeypatch):

        mock_mkdtemp = MagicMock(return_value="/tmp/path")
        mock_makedirs = MagicMock(side_effect=OSError("Some OS Error here"))

        monkeypatch.setattr(tempfile, 'mkdtemp', mock_mkdtemp)
        monkeypatch.setattr(os.path, 'exists', lambda x: False)
        monkeypatch.setattr(os, 'makedirs', mock_makedirs)

        actual = am.tmpdir
        assert actual == "/tmp/path"
        assert mock_makedirs.call_args[0] == (os.path.expanduser(os.path.expandvars("$HOME/.test")),)
        assert mock_makedirs.call_args[1] == {"mode": 0o700}

        # because makedirs failed the dir should be None so it uses the System tmp
        assert mock_mkdtemp.call_args[1]['dir'] is None
        assert mock_mkdtemp.call_args[1]['prefix'].startswith("ansible-moduletmp-")

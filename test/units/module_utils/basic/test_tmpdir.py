# -*- coding: utf-8 -*-
# Copyright (c) 2015-2018 Ansible Project
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

    @pytest.mark.parametrize('stdin', ({"_ansible_tmpdir": '/path/to/dir',
                                        "_ansible_remote_tmp": '/path/tmpdir',
                                        "_ansible_keep_remote_files": False},),
                             indirect=['stdin'])
    def test_tmpdir_passed_in(self, am):
        assert am._tmpdir == '/path/to/dir'
        assert am.tmpdir == '/path/to/dir'
        assert am._remote_tmp == '/path/tmpdir'

    @pytest.mark.parametrize('stdin', ({"_ansible_tmpdir": None,
                                        "_ansible_remote_tmp": '/path/tmpdir',
                                        "_ansible_keep_remote_files": False},),
                             indirect=['stdin'])
    def test_tmpdir_not_passed_in(self, am, monkeypatch):
        def mock_mkdtemp(prefix, dir):
            return os.path.join(dir, prefix)
        monkeypatch.setattr(tempfile, 'mkdtemp', mock_mkdtemp)
        monkeypatch.setattr(shutil, 'rmtree', lambda x: None)

        assert am._tmpdir is None
        assert am._remote_tmp == '/path/tmpdir'

        with patch('time.time', return_value=42):
            actual_tmpdir = am.tmpdir
        assert actual_tmpdir == '/path/tmpdir/ansible-moduletmp-42-'
        assert am._tmpdir == actual_tmpdir

        # verify subsequent calls always produces the same tmpdir
        assert am.tmpdir == actual_tmpdir

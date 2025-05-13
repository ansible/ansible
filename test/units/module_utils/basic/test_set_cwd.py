# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import tempfile

from unittest.mock import patch

from ansible.module_utils import basic
from ansible.module_utils.testing import patch_module_args


class TestAnsibleModuleSetCwd:

    def test_set_cwd(self, monkeypatch):

        """make sure /tmp is used"""

        def mock_getcwd():
            return '/tmp'

        def mock_access(path, perm):
            return True

        def mock_chdir(path):
            pass

        monkeypatch.setattr(os, 'getcwd', mock_getcwd)
        monkeypatch.setattr(os, 'access', mock_access)

        with patch_module_args(), \
             patch('time.time', return_value=42):
            am = basic.AnsibleModule(argument_spec={})

        result = am._set_cwd()
        assert result == '/tmp'

    def test_set_cwd_unreadable_use_self_tmpdir(self, monkeypatch):

        """pwd is not readable, use instance's tmpdir property"""

        def mock_getcwd():
            return '/tmp'

        def mock_access(path, perm):
            if path == '/tmp' and perm == 4:
                return False
            return True

        def mock_expandvars(var):
            if var == '$HOME':
                return '/home/foobar'
            return var

        def mock_gettempdir():
            return '/tmp/testdir'

        def mock_chdir(path):
            if path == '/tmp':
                raise Exception()
            return

        monkeypatch.setattr(os, 'getcwd', mock_getcwd)
        monkeypatch.setattr(os, 'chdir', mock_chdir)
        monkeypatch.setattr(os, 'access', mock_access)
        monkeypatch.setattr(os.path, 'expandvars', mock_expandvars)

        with patch_module_args(), \
             patch('time.time', return_value=42):
            am = basic.AnsibleModule(argument_spec={})

        am._tmpdir = '/tmp2'
        result = am._set_cwd()
        assert result == am._tmpdir

    def test_set_cwd_unreadable_use_home(self, monkeypatch):

        """cwd and instance tmpdir are unreadable, use home"""

        def mock_getcwd():
            return '/tmp'

        def mock_access(path, perm):
            if path in ['/tmp', '/tmp2'] and perm == 4:
                return False
            return True

        def mock_expandvars(var):
            if var == '$HOME':
                return '/home/foobar'
            return var

        def mock_gettempdir():
            return '/tmp/testdir'

        def mock_chdir(path):
            if path == '/tmp':
                raise Exception()
            return

        monkeypatch.setattr(os, 'getcwd', mock_getcwd)
        monkeypatch.setattr(os, 'chdir', mock_chdir)
        monkeypatch.setattr(os, 'access', mock_access)
        monkeypatch.setattr(os.path, 'expandvars', mock_expandvars)

        with patch_module_args(), \
             patch('time.time', return_value=42):
            am = basic.AnsibleModule(argument_spec={})

        am._tmpdir = '/tmp2'
        result = am._set_cwd()
        assert result == '/home/foobar'

    def test_set_cwd_unreadable_use_gettempdir(self, monkeypatch):

        """fallback to tempfile.gettempdir"""

        thisdir = None

        def mock_getcwd():
            return '/tmp'

        def mock_access(path, perm):
            if path in ['/tmp', '/tmp2', '/home/foobar'] and perm == 4:
                return False
            return True

        def mock_expandvars(var):
            if var == '$HOME':
                return '/home/foobar'
            return var

        def mock_gettempdir():
            return '/tmp3'

        def mock_chdir(path):
            if path == '/tmp':
                raise Exception()
            thisdir = path

        monkeypatch.setattr(os, 'getcwd', mock_getcwd)
        monkeypatch.setattr(os, 'chdir', mock_chdir)
        monkeypatch.setattr(os, 'access', mock_access)
        monkeypatch.setattr(os.path, 'expandvars', mock_expandvars)

        with patch_module_args(), \
             patch('time.time', return_value=42):
            am = basic.AnsibleModule(argument_spec={})

        am._tmpdir = '/tmp2'
        monkeypatch.setattr(tempfile, 'gettempdir', mock_gettempdir)
        result = am._set_cwd()
        assert result == '/tmp3'

    def test_set_cwd_unreadable_use_None(self, monkeypatch):

        """all paths are unreable, should return None and not an exception"""

        def mock_getcwd():
            return '/tmp'

        def mock_access(path, perm):
            if path in ['/tmp', '/tmp2', '/tmp3', '/home/foobar'] and perm == 4:
                return False
            return True

        def mock_expandvars(var):
            if var == '$HOME':
                return '/home/foobar'
            return var

        def mock_gettempdir():
            return '/tmp3'

        def mock_chdir(path):
            if path == '/tmp':
                raise Exception()

        monkeypatch.setattr(os, 'getcwd', mock_getcwd)
        monkeypatch.setattr(os, 'chdir', mock_chdir)
        monkeypatch.setattr(os, 'access', mock_access)
        monkeypatch.setattr(os.path, 'expandvars', mock_expandvars)

        with patch_module_args(), \
             patch('time.time', return_value=42):
            am = basic.AnsibleModule(argument_spec={})

        am._tmpdir = '/tmp2'
        monkeypatch.setattr(tempfile, 'gettempdir', mock_gettempdir)
        result = am._set_cwd()
        assert result is None

# -*- coding: utf-8 -*-
# (c) 2017 Toshio Kuratomi <tkuratomi@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pwd
import os

import pytest

from ansible import constants
from ansible.module_utils.six import StringIO
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_text


@pytest.fixture
def cfgparser():
    CFGDATA = StringIO("""
[defaults]
defaults_one = 'data_defaults_one'

[level1]
level1_one = 'data_level1_one'
    """)
    p = configparser.ConfigParser()
    p.readfp(CFGDATA)
    return p


@pytest.fixture
def user():
    user = {}
    user['uid'] = os.geteuid()

    pwd_entry = pwd.getpwuid(user['uid'])
    user['username'] = pwd_entry.pw_name
    user['home'] = pwd_entry.pw_dir

    return user


@pytest.fixture
def cfg_file():
    data = '/ansible/test/cfg/path'
    old_cfg_file = constants.CONFIG_FILE
    constants.CONFIG_FILE = os.path.join(data, 'ansible.cfg')
    yield data

    constants.CONFIG_FILE = old_cfg_file


@pytest.fixture
def null_cfg_file():
    old_cfg_file = constants.CONFIG_FILE
    del constants.CONFIG_FILE
    yield

    constants.CONFIG_FILE = old_cfg_file


@pytest.fixture
def cwd():
    data = '/ansible/test/cwd/'
    old_cwd = os.getcwd
    os.getcwd = lambda: data

    old_cwdu = None
    if hasattr(os, 'getcwdu'):
        old_cwdu = os.getcwdu
        os.getcwdu = lambda: to_text(data)

    yield data

    os.getcwd = old_cwd
    if hasattr(os, 'getcwdu'):
        os.getcwdu = old_cwdu


class TestMkBoolean:
    def test_bools(self):
        assert constants.mk_boolean(True) is True
        assert constants.mk_boolean(False) is False

    def test_none(self):
        assert constants.mk_boolean(None) is False

    def test_numbers(self):
        assert constants.mk_boolean(1) is True
        assert constants.mk_boolean(0) is False
        assert constants.mk_boolean(0.0) is False

# Current mk_boolean doesn't consider these to be true values
#    def test_other_numbers(self):
#        assert constants.mk_boolean(2) is True
#        assert constants.mk_boolean(-1) is True
#        assert constants.mk_boolean(0.1) is True

    def test_strings(self):
        assert constants.mk_boolean("true") is True
        assert constants.mk_boolean("TRUE") is True
        assert constants.mk_boolean("t") is True
        assert constants.mk_boolean("yes") is True
        assert constants.mk_boolean("y") is True
        assert constants.mk_boolean("on") is True

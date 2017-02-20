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
from __future__ import (absolute_import, division)
__metaclass__ = type

import pwd
import os

import pytest

from ansible import constants
from ansible.compat.six import StringIO
from ansible.compat.six.moves import configparser
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
    os.getcwd = lambda : data

    old_cwdu = None
    if hasattr(os, 'getcwdu'):
        old_cwdu = os.getcwdu
        os.getcwdu = lambda : to_text(data)

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


class TestShellExpand:
    def test_shell_expand_none(self):
        assert constants.shell_expand(None) is None

    def test_shell_expand_static_path(self):
        assert constants.shell_expand(u'/usr/local') == u'/usr/local'

    def test_shell_expand_tilde(self, user):
        assert constants.shell_expand(u'~/local') == os.path.join(user['home'], 'local')
        assert constants.shell_expand(u'~%s/local' % user['username']) == os.path.join(user['home'], 'local')

    def test_shell_expand_vars(self, user):
        assert constants.shell_expand(u'$HOME/local') == os.path.join(user['home'], 'local')

        os.environ['ANSIBLE_TEST_VAR'] = '/srv/ansible'
        assert constants.shell_expand(u'$ANSIBLE_TEST_VAR/local') == os.path.join('/srv/ansible', 'local')

        os.environ['ANSIBLE_TEST_VAR'] = '~'
        assert constants.shell_expand(u'$ANSIBLE_TEST_VAR/local') == os.path.join(user['home'], 'local')

        del os.environ['ANSIBLE_TEST_VAR']
        assert constants.shell_expand(u'$ANSIBLE_TEST_VAR/local') == u'$ANSIBLE_TEST_VAR/local'

    def test_expand_relative_abs_path(self):
        assert constants.shell_expand('/absolute/path', expand_relative_paths=True) == '/absolute/path'

    def test_expand_relative_path_relative_cfg_file(self, cfg_file):
        assert constants.shell_expand(u'relative/path', expand_relative_paths=True) == os.path.join(cfg_file, 'relative/path')

    def test_expand_relative_path_relative_cwd(self, cwd, null_cfg_file):
        assert constants.shell_expand(u'relative/path', expand_relative_paths=True) == os.path.join(cwd, 'relative/path')


# configparser object
class TestGetConfig:
    def test_from_config_file(self, cfgparser):
        assert constants.get_config(cfgparser, 'defaults', 'defaults_one', 'ANSIBLE_TEST_VAR', 'foo', value_type=None) == 'data_defaults_one'
        assert constants.get_config(cfgparser, 'level1', 'level1_one', 'ANSIBLE_TEST_VAR', 'foo', value_type=None) == 'data_level1_one'

    def test_from_env_var(self, cfgparser):
        os.environ['ANSIBLE_TEST_VAR'] = 'bar'

        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 'foo', value_type=None) == 'bar'
        assert constants.get_config(cfgparser, 'unknown', 'defaults_one', 'ANSIBLE_TEST_VAR', 'foo', value_type=None) == 'bar'

        del os.environ['ANSIBLE_TEST_VAR']

    def test_from_default(self, cfgparser):
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 'foo', value_type=None) == u'foo'
        assert constants.get_config(cfgparser, 'unknown', 'defaults_one', 'ANSIBLE_TEST_VAR', 'foo', value_type=None) == u'foo'

    def test_value_type_boolean(self, cfgparser):
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 'on', value_type='boolean') is True
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', True, value_type='boolean') is True
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 'other', value_type='boolean') is False

    def test_value_type_integer(self, cfgparser):
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', '10', value_type='integer') == 10
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 10, value_type='integer') == 10

    def test_value_type_float(self, cfgparser):
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', '10', value_type='float') == 10.0
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 10, value_type='float') == 10.0
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', '11.5', value_type='float') == 11.5
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 11.5, value_type='float') == 11.5

    def test_value_type_list(self, cfgparser):
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 'one,two,three', value_type='list') == ['one', 'two', 'three']
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', ['one', 'two', 'three'], value_type='list') == ['one', 'two', 'three']

    def test_value_type_none(self, cfgparser):
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 'None', value_type='none') is None
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', None, value_type='none') is None

    def test_value_type_path(self, cfgparser, user, cfg_file):
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', '~/local', value_type='path') == os.path.join(user['home'], 'local')
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 'local', value_type='path') == 'local'
        assert constants.get_config(cfgparser, 'defaults', 'unknown', 'ANSIBLE_TEST_VAR', 'local', value_type='path', expand_relative_paths=True) \
                == os.path.join(cfg_file, 'local')

# Need to implement tests for these
#    def test_value_type_pathlist(self, cfgparser):
#        pass
#
#    def test_value_type_string(self, cfgparser):
#        pass
#
#    def test_value_type_temppath(self, cfgparser):
#        pass


# Need to test this
#def test_load_config_file():
#    pass


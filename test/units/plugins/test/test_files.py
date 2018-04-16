# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os
import os.path

from ansible.compat.tests import unittest
from ansible.plugins.test.files import expand_path_wrap


class TestExpandPathWrap(unittest.TestCase):

    dirname = '~/.testing_dir_test_files'

    @classmethod
    def setUpClass(cls):
        os.mkdir(os.path.expanduser(cls.dirname))

    @classmethod
    def tearDownClass(cls):
        os.rmdir(os.path.expanduser(cls.dirname))

    def test_expand_path_wrap_isdir_one_arg(self):
        func = expand_path_wrap(os.path.isdir)
        self.assertTrue(func(self.dirname))

    def test_expand_path_wrap_is_same_file_two_args(self):
        func = expand_path_wrap(os.path.samefile)
        self.assertTrue(func(self.dirname, self.dirname))

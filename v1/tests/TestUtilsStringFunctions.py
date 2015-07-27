# -*- coding: utf-8 -*-

import unittest
import os
import os.path
import tempfile
import yaml
import passlib.hash
import string
import StringIO
import copy

from nose.plugins.skip import SkipTest

from ansible.utils import string_functions
import ansible.errors
import ansible.constants as C
import ansible.utils.template as template2

from ansible import __version__

import sys
reload(sys)
sys.setdefaultencoding("utf8") 

class TestUtilsStringFunctions(unittest.TestCase):
    def test_isprintable(self):
        self.assertFalse(string_functions.isprintable(chr(7)))
        self.assertTrue(string_functions.isprintable('hello'))

    def test_count_newlines_from_end(self):
        self.assertEqual(string_functions.count_newlines_from_end('foo\n\n\n\n'), 4)
        self.assertEqual(string_functions.count_newlines_from_end('\nfoo'), 0)

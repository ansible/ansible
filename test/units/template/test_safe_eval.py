# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import sys
from collections import defaultdict

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.template.safe_eval import safe_eval


class TestSafeEval(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_safe_eval_usage(self):
        # test safe eval calls with different possible types for the
        # locals dictionary, to ensure we don't run into problems like
        # ansible/ansible/issues/12206 again
        for locals_vars in (dict(), defaultdict(dict)):
            self.assertEqual(safe_eval('True', locals=locals_vars), True)
            self.assertEqual(safe_eval('False', locals=locals_vars), False)
            self.assertEqual(safe_eval('0', locals=locals_vars), 0)
            self.assertEqual(safe_eval('[]', locals=locals_vars), [])
            self.assertEqual(safe_eval('{}', locals=locals_vars), {})

    @unittest.skipUnless(sys.version_info[:2] >= (2, 7), "Python 2.6 has no set literals")
    def test_set_literals(self):
        self.assertEqual(safe_eval('{0}'), set([0]))

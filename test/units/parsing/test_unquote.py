# coding: utf-8
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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

from nose import tools
from ansible.compat.tests import unittest

from ansible.parsing.quoting import unquote


# Tests using nose's test generators cannot use unittest base class.
# http://nose.readthedocs.org/en/latest/writing_tests.html#test-generators
class TestUnquote:
    UNQUOTE_DATA = (
            (u'1', u'1'),
            (u'\'1\'', u'1'),
            (u'"1"', u'1'),
            (u'"1 \'2\'"', u'1 \'2\''),
            (u'\'1 "2"\'', u'1 "2"'),
            (u'\'1 \'2\'\'', u'1 \'2\''),
            (u'"1\\"', u'"1\\"'),
            (u'\'1\\\'', u'\'1\\\''),
            (u'"1 \\"2\\" 3"', u'1 \\"2\\" 3'),
            (u'\'1 \\\'2\\\' 3\'', u'1 \\\'2\\\' 3'),
            (u'"', u'"'),
            (u'\'', u'\''),
            # Not entirely sure these are good but they match the current
            # behaviour
            (u'"1""2"', u'1""2'),
            (u'\'1\'\'2\'', u'1\'\'2'),
            (u'"1" 2 "3"', u'1" 2 "3'),
            (u'"1"\'2\'"3"', u'1"\'2\'"3'),
            )

    def check_unquote(self, quoted, expected):
        tools.eq_(unquote(quoted), expected)

    def test_unquote(self):
        for datapoint in self.UNQUOTE_DATA:
            yield self.check_unquote, datapoint[0], datapoint[1]

# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
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

import pytest

import ansible.errors

from ansible.executor import module_common as amc
from ansible.module_utils.six import PY2


class TestStripComments(object):
    def test_no_changes(self):
        no_comments = u"""def some_code():
    return False"""
        assert amc._strip_comments(no_comments) == no_comments

    def test_all_comments(self):
        all_comments = u"""# This is a test
            # Being as it is
            # To be
            """
        assert amc._strip_comments(all_comments) == u""

    def test_all_whitespace(self):
        # Note: Do not remove the spaces on the blank lines below.  They're
        # test data to show that the lines get removed despite having spaces
        # on them
        all_whitespace = u"""
              

                
\t\t\r\n
            """  # nopep8
        assert amc._strip_comments(all_whitespace) == u""

    def test_somewhat_normal(self):
        mixed = u"""#!/usr/bin/python

# here we go
def test(arg):
    # this is a thing
    thing = '# test'
    return thing
# End
"""
        mixed_results = u"""def test(arg):
    thing = '# test'
    return thing"""
        assert amc._strip_comments(mixed) == mixed_results


class TestSlurp(object):
    def test_slurp_nonexistent(self, mocker):
        mocker.patch('os.path.exists', side_effect=lambda x: False)
        with pytest.raises(ansible.errors.AnsibleError):
            amc._slurp('no_file')

    def test_slurp_file(self, mocker):
        mocker.patch('os.path.exists', side_effect=lambda x: True)
        m = mocker.mock_open(read_data='This is a test')
        if PY2:
            mocker.patch('__builtin__.open', m)
        else:
            mocker.patch('builtins.open', m)
        assert amc._slurp('some_file') == 'This is a test'

    def test_slurp_file_with_newlines(self, mocker):
        mocker.patch('os.path.exists', side_effect=lambda x: True)
        m = mocker.mock_open(read_data='#!/usr/bin/python\ndef test(args):\nprint("hi")\n')
        if PY2:
            mocker.patch('__builtin__.open', m)
        else:
            mocker.patch('builtins.open', m)
        assert amc._slurp('some_file') == '#!/usr/bin/python\ndef test(args):\nprint("hi")\n'


@pytest.fixture
def templar():
    class FakeTemplar(object):
        def template(self, template_string, *args, **kwargs):
            return template_string

    return FakeTemplar()


class TestGetShebang(object):
    """Note: We may want to change the API of this function in the future.  It isn't a great API"""
    def test_no_interpreter_set(self, templar):
        assert amc._get_shebang(u'/usr/bin/python', {}, templar) == (None, u'/usr/bin/python')

    def test_non_python_interpreter(self, templar):
        assert amc._get_shebang(u'/usr/bin/ruby', {}, templar) == (None, u'/usr/bin/ruby')

    def test_interpreter_set_in_task_vars(self, templar):
        assert amc._get_shebang(u'/usr/bin/python', {u'ansible_python_interpreter': u'/usr/bin/pypy'}, templar) == \
            (u'#!/usr/bin/pypy', u'/usr/bin/pypy')

    def test_non_python_interpreter_in_task_vars(self, templar):
        assert amc._get_shebang(u'/usr/bin/ruby', {u'ansible_ruby_interpreter': u'/usr/local/bin/ruby'}, templar) == \
            (u'#!/usr/local/bin/ruby', u'/usr/local/bin/ruby')

    def test_with_args(self, templar):
        assert amc._get_shebang(u'/usr/bin/python', {u'ansible_python_interpreter': u'/usr/bin/python3'}, templar, args=('-tt', '-OO')) == \
            (u'#!/usr/bin/python3 -tt -OO', u'/usr/bin/python3')

    def test_python_via_env(self, templar):
        assert amc._get_shebang(u'/usr/bin/python', {u'ansible_python_interpreter': u'/usr/bin/env python'}, templar) == \
            (u'#!/usr/bin/env python', u'/usr/bin/env python')

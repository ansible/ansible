# (c) 2016, Matt Davis <mdavis@ansible.com>
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

from contextlib import contextmanager
from io import BytesIO, StringIO
from ansible.compat.six import PY3
from ansible.utils.unicode import to_bytes

@contextmanager
def swap_stdin_and_argv(stdin_data='', argv_data=tuple()):
    """
    context manager that temporarily masks the test runner's values for stdin and argv
    """
    real_stdin = sys.stdin

    if PY3:
        sys.stdin = StringIO(stdin_data)
        sys.stdin.buffer = BytesIO(to_bytes(stdin_data))
    else:
        sys.stdin = BytesIO(to_bytes(stdin_data))

    real_argv = sys.argv
    sys.argv = argv_data
    yield
    sys.stdin = real_stdin
    sys.argv = real_argv

@contextmanager
def swap_stdout():
    """
    context manager that temporarily replaces stdout for tests that need to verify output
    """
    old_stdout = sys.stdout
    fake_stream = BytesIO()
    sys.stdout = fake_stream
    yield fake_stream
    sys.stdout = old_stdout
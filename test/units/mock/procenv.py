# (c) 2016, Matt Davis <mdavis@ansible.com>
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
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

from __future__ import annotations

import sys
import json

from contextlib import contextmanager
from io import BytesIO, StringIO
import unittest
from ansible.module_utils.common.text.converters import to_bytes


@contextmanager
def swap_stdin_and_argv(stdin_data='', argv_data=tuple()):
    """
    context manager that temporarily masks the test runner's values for stdin and argv
    """
    real_stdin = sys.stdin
    real_argv = sys.argv

    fake_stream = StringIO(stdin_data)
    fake_stream.buffer = BytesIO(to_bytes(stdin_data))

    try:
        sys.stdin = fake_stream
        sys.argv = argv_data

        yield
    finally:
        sys.stdin = real_stdin
        sys.argv = real_argv


class ModuleTestCase(unittest.TestCase):
    def setUp(self):
        module_args = {'_ansible_remote_tmp': '/tmp', '_ansible_keep_remote_files': False}

        args = json.dumps(dict(ANSIBLE_MODULE_ARGS=module_args))

        # unittest doesn't have a clean place to use a context manager, so we have to enter/exit manually
        self.stdin_swap = swap_stdin_and_argv(stdin_data=args)
        self.stdin_swap.__enter__()

    def tearDown(self):
        # unittest doesn't have a clean place to use a context manager, so we have to enter/exit manually
        self.stdin_swap.__exit__(None, None, None)

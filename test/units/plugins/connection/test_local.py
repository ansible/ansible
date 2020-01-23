#
# (c) 2020 Red Hat Inc.
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

from io import StringIO
import pytest
import shutil
import tempfile

from units.compat import unittest
from ansible.errors import AnsibleFileNotFound
from ansible.plugins.connection import local
from ansible.playbook.play_context import PlayContext


class TestLocalConnectionClass(unittest.TestCase):

    def test_local_connection_module(self):
        play_context = PlayContext()
        play_context.prompt = (
            '[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: '
        )
        in_stream = StringIO()

        conn = local.Connection(play_context, in_stream)
        self.assertIsInstance(conn, local.Connection)

        # Ensure that file paths are encoded properly
        tempdir = tempfile.mkdtemp()
        conn.cwd = tempdir.encode('utf-8')  # action plugin sets the cwd as 'bytes'
        try:
            self.assertRaises(AnsibleFileNotFound, conn.put_file, "source", "destination")
        finally:
            shutil.rmtree(tempdir)

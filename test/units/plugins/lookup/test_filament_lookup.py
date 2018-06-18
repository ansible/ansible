# -*- coding: utf-8 -*-
# (c) 2018, Zhikang Zhang <zhikzhan@redhat.com>
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
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import subprocess

from ansible.errors import AnsibleError
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import MagicMock, patch
import ansible.plugins.lookup.filament_lookup as filament_lookup


class FakeBuffer:
    def __init__(self, string):
        self.content = string

    def read(self):
        return self.content


class FakeProcess:
    def __init__(self, string):
        self.stdout = FakeBuffer(string)


def popen_side_effect(command, **kwargs):
    if command.startswith("ps aux|grep"):
        index = command.find("grep")
        result = command[index + 5:] + " Process"
        return FakeProcess(result)
    else:
        return FakeProcess("Many processes")


class TestFilamentLookup(unittest.TestCase):

    @patch('subprocess.Popen')
    def test_run_command_one_arg(self, test_patch):
        test_patch.side_effect = popen_side_effect
        result = filament_lookup.run_command(['python'])
        self.assertEqual('python Process', result)

    @patch('subprocess.Popen')
    def test_run_command_no_arg(self, test_patch):
        test_patch.side_effect = popen_side_effect
        result = filament_lookup.run_command(None)
        self.assertEqual('Many processes', result)

    @patch('subprocess.Popen')
    def test_run_command_three_arg(self, test_patch):
        try:
            test_patch.side_effect = popen_side_effect
            result = filament_lookup.run_command(['bad', 'arguments'])
            self.fail()
        except AnsibleError:
            pass

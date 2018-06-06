# -*- coding: utf-8 -*-
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

from units.mock.loader import DictDataLoader

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import MagicMock
from ansible.plugins.lookup.filament_lookup import run_command
import subprocess


def popen_side_effect(command, **kwargs):
    if command.startswith("ps aux|grep"):
        index = command.find("grep")
        return command[index+5:]  + " Process"
    else:
        return "Many processes"


class TestFilamentLookup(unittest.TestCase):
    
    def test_run_command_one_arg(self):
        subprocess.Popen = MagicMock(side_effect=popen_side_effect)
        result = run_command(['python'])
        self.assertEqual('python Process',result)

    def test_run_command_no_arg(self):
        pass

    def test_run_command_three_arg(self):
        pass
	



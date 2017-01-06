# (c) 2016, Pierre-Gildas MILLON <pgmillon@gmail.com>
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

import os
from ansible import constants
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

original_open = open
original_getenv = os.getenv


def open(path):
    if "/etc/ansible/ansible.cfg" == path:
        return TestLoadConfiguration.open_resource("resources/01-etc.cfg")
    if os.path.expanduser("~/.ansible.cfg") == path:
        return TestLoadConfiguration.open_resource("resources/02-user.cfg")
    if os.getcwd() + "/ansible.cfg" == path:
        return TestLoadConfiguration.open_resource("resources/03-cwd.cfg")
    if "resources/ansible.cfg" == path:
        return TestLoadConfiguration.open_resource("resources/04-env.cfg")


def getenv(key, default=None):
    if "ANSIBLE_CONFIG" == key:
        return "resources/ansible.cfg"
    return original_getenv(key, default)


def exists(_):
    return True


class TestLoadConfiguration(unittest.TestCase):

    @staticmethod
    def open_resource(path):
        path = os.path.dirname(os.path.abspath(__file__)) + '/' + path
        return original_open(path)

    @patch('__builtin__.open', open)
    @patch('os.getenv', getenv)
    @patch('os.path.exists', exists)
    def test_load_config(self):
        p, config_file = constants.load_config_file()

        self.assertEqual(1, p.getint("defaults", "etc_only"))
        self.assertEqual(2, p.getint("defaults", "user"))
        self.assertEqual(3, p.getint("defaults", "cwd"))
        self.assertEqual(4, p.getint("defaults", "etc"))
        self.assertEqual(4, p.getint("defaults", "env"))

        self.assertEqual("resources/ansible.cfg", config_file)

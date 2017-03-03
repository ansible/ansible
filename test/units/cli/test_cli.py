# (c) 2017, Adrian Likins <alikins@redhat.com>
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

from ansible.compat.tests import unittest

from ansible.release import __version__
from ansible import cli


class TestCliVersion(unittest.TestCase):

    def test_version(self):
        ver = cli.CLI.version('ansible-cli-test')
        self.assertIn('ansible-cli-test', ver)
        self.assertIn('python version', ver)

    def test_version_info(self):
        version_info = cli.CLI.version_info()
        self.assertEqual(version_info['string'], __version__)

    def test_version_info_gitinfo(self):
        version_info = cli.CLI.version_info(gitinfo=True)
        self.assertIn('python version', version_info['string'])

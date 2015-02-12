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

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible.vars import VariableManager

from test.mock.loader import DictDataLoader

class TestVariableManager(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_basic_manager(self):
        v = VariableManager()
        self.assertEqual(v.get_vars(), dict())

        self.assertEqual(
            v._merge_dicts(
                dict(a=1),
                dict(b=2)
            ), dict(a=1, b=2)
        )
        self.assertEqual(
            v._merge_dicts(
                dict(a=1, c=dict(foo='bar')),
                dict(b=2, c=dict(baz='bam'))
            ), dict(a=1, b=2, c=dict(foo='bar', baz='bam'))
        )


    def test_manager_extra_vars(self):
        extra_vars = dict(a=1, b=2, c=3)
        v = VariableManager()
        v.set_extra_vars(extra_vars)

        self.assertEqual(v.get_vars(), extra_vars)
        self.assertIsNot(v.extra_vars, extra_vars)

    def test_manager_host_vars_file(self):
        fake_loader = DictDataLoader({
            "host_vars/hostname1.yml": """
               foo: bar
            """
        })

        v = VariableManager(loader=fake_loader)
        v.add_host_vars_file("host_vars/hostname1.yml")
        self.assertIn("hostname1", v._host_vars_files)
        self.assertEqual(v._host_vars_files["hostname1"], dict(foo="bar"))

        mock_host = MagicMock()
        mock_host.get_name.return_value = "hostname1"
        mock_host.get_vars.return_value = dict()
        mock_host.get_groups.return_value = ()

        self.assertEqual(v.get_vars(host=mock_host), dict(foo="bar"))

    def test_manager_group_vars_file(self):
        fake_loader = DictDataLoader({
            "group_vars/somegroup.yml": """
               foo: bar
            """
        })

        v = VariableManager(loader=fake_loader)
        v.add_group_vars_file("group_vars/somegroup.yml")
        self.assertIn("somegroup", v._group_vars_files)
        self.assertEqual(v._group_vars_files["somegroup"], dict(foo="bar"))

        mock_host = MagicMock()
        mock_host.get_name.return_value = "hostname1"
        mock_host.get_vars.return_value = dict()
        mock_host.get_groups.return_value = ["somegroup"]

        self.assertEqual(v.get_vars(host=mock_host), dict(foo="bar"))

    def test_manager_play_vars(self):
        mock_play = MagicMock()
        mock_play.get_vars.return_value = dict(foo="bar")
        mock_play.get_roles.return_value = []
        mock_play.get_vars_files.return_value = []

        v = VariableManager()
        self.assertEqual(v.get_vars(play=mock_play), dict(foo="bar"))

    def test_manager_play_vars_files(self):
        fake_loader = DictDataLoader({
            "/path/to/somefile.yml": """
               foo: bar
            """
        })

        mock_play = MagicMock()
        mock_play.get_vars.return_value = dict()
        mock_play.get_roles.return_value = []
        mock_play.get_vars_files.return_value = ['/path/to/somefile.yml']

        v = VariableManager(loader=fake_loader)
        self.assertEqual(v.get_vars(play=mock_play), dict(foo="bar"))

    def test_manager_task_vars(self):
        mock_task = MagicMock()
        mock_task.get_vars.return_value = dict(foo="bar")

        v = VariableManager()
        self.assertEqual(v.get_vars(task=mock_task), dict(foo="bar"))


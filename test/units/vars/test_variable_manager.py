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

from collections import defaultdict
from six import iteritems

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.vars import VariableManager

from units.mock.loader import DictDataLoader

class TestVariableManager(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_basic_manager(self):
        fake_loader = DictDataLoader({})

        v = VariableManager()
        vars = v.get_vars(loader=fake_loader, use_cache=False)
        if 'omit' in vars:
            del vars['omit']
        if 'vars' in vars:
            del vars['vars']
        if 'ansible_version' in vars:
            del vars['ansible_version']

        self.assertEqual(vars, dict(playbook_dir='.'))

    def test_variable_manager_extra_vars(self):
        fake_loader = DictDataLoader({})

        extra_vars = dict(a=1, b=2, c=3)
        v = VariableManager()
        v.extra_vars = extra_vars

        vars = v.get_vars(loader=fake_loader, use_cache=False)

        for (key, val) in iteritems(extra_vars):
            self.assertEqual(vars.get(key), val)

        self.assertIsNot(v.extra_vars, extra_vars)

    def test_variable_manager_host_vars_file(self):
        fake_loader = DictDataLoader({
            "host_vars/hostname1.yml": """
               foo: bar
            """,
            "other_path/host_vars/hostname1.yml": """
               foo: bam
               baa: bat
            """,
            "host_vars/host.name.yml": """
               host_with_dots: true
            """,
        })

        v = VariableManager()
        v.add_host_vars_file("host_vars/hostname1.yml", loader=fake_loader)
        v.add_host_vars_file("other_path/host_vars/hostname1.yml", loader=fake_loader)
        self.assertIn("hostname1", v._host_vars_files)
        self.assertEqual(v._host_vars_files["hostname1"], [dict(foo="bar"), dict(foo="bam", baa="bat")])

        mock_host = MagicMock()
        mock_host.get_name.return_value = "hostname1"
        mock_host.get_vars.return_value = dict()
        mock_host.get_groups.return_value = ()
        mock_host.get_group_vars.return_value = dict()

        self.assertEqual(v.get_vars(loader=fake_loader, host=mock_host, use_cache=False).get("foo"), "bam")
        self.assertEqual(v.get_vars(loader=fake_loader, host=mock_host, use_cache=False).get("baa"), "bat")

        v.add_host_vars_file("host_vars/host.name", loader=fake_loader)
        self.assertEqual(v._host_vars_files["host.name"], [dict(host_with_dots=True)])

    def test_variable_manager_group_vars_file(self):
        fake_loader = DictDataLoader({
            "group_vars/all.yml": """
               foo: bar
            """,
            "group_vars/somegroup.yml": """
               bam: baz
            """,
            "other_path/group_vars/somegroup.yml": """
               baa: bat
            """,
            "group_vars/some.group.yml": """
               group_with_dots: true
            """,
        })

        v = VariableManager()
        v.add_group_vars_file("group_vars/all.yml", loader=fake_loader)
        v.add_group_vars_file("group_vars/somegroup.yml", loader=fake_loader)
        v.add_group_vars_file("other_path/group_vars/somegroup.yml", loader=fake_loader)
        self.assertIn("somegroup", v._group_vars_files)
        self.assertEqual(v._group_vars_files["all"], [dict(foo="bar")])
        self.assertEqual(v._group_vars_files["somegroup"], [dict(bam="baz"), dict(baa="bat")])

        mock_group = MagicMock()
        mock_group.name = "somegroup"
        mock_group.get_ancestors.return_value = ()
        mock_group.get_vars.return_value = dict()

        mock_host = MagicMock()
        mock_host.get_name.return_value = "hostname1"
        mock_host.get_vars.return_value = dict()
        mock_host.get_groups.return_value = (mock_group,)
        mock_host.get_group_vars.return_value = dict()

        vars = v.get_vars(loader=fake_loader, host=mock_host, use_cache=False)
        self.assertEqual(vars.get("foo"), "bar")
        self.assertEqual(vars.get("baa"), "bat")

        v.add_group_vars_file("group_vars/some.group", loader=fake_loader)
        self.assertEqual(v._group_vars_files["some.group"], [dict(group_with_dots=True)])

    def test_variable_manager_play_vars(self):
        fake_loader = DictDataLoader({})

        mock_play = MagicMock()
        mock_play.get_vars.return_value = dict(foo="bar")
        mock_play.get_roles.return_value = []
        mock_play.get_vars_files.return_value = []

        v = VariableManager()
        self.assertEqual(v.get_vars(loader=fake_loader, play=mock_play, use_cache=False).get("foo"), "bar")

    def test_variable_manager_play_vars_files(self):
        fake_loader = DictDataLoader({
            "/path/to/somefile.yml": """
               foo: bar
            """
        })

        mock_play = MagicMock()
        mock_play.get_vars.return_value = dict()
        mock_play.get_roles.return_value = []
        mock_play.get_vars_files.return_value = ['/path/to/somefile.yml']

        v = VariableManager()
        self.assertEqual(v.get_vars(loader=fake_loader, play=mock_play, use_cache=False).get("foo"), "bar")

    def test_variable_manager_task_vars(self):
        fake_loader = DictDataLoader({})

        mock_task = MagicMock()
        mock_task._role = None
        mock_task.loop = None
        mock_task.get_vars.return_value = dict(foo="bar")
        mock_task.get_include_params.return_value = dict()

        v = VariableManager()
        self.assertEqual(v.get_vars(loader=fake_loader, task=mock_task, use_cache=False).get("foo"), "bar")

    @patch.object(Inventory, 'basedir')
    def test_variable_manager_precedence(self, mock_basedir):
        '''
        Tests complex variations and combinations of get_vars() with different
        objects to modify the context under which variables are merged.
        '''

        v = VariableManager()
        v._fact_cache = defaultdict(dict)

        fake_loader = DictDataLoader({
            # inventory1
            '/etc/ansible/inventory1': """
            [group2:children]
            group1

            [group1]
            host1 host_var=host_var_from_inventory_host1

            [group1:vars]
            group_var = group_var_from_inventory_group1

            [group2:vars]
            group_var = group_var_from_inventory_group2
            """,

            # role defaults_only1
            '/etc/ansible/roles/defaults_only1/defaults/main.yml': """
            default_var: "default_var_from_defaults_only1"
            host_var: "host_var_from_defaults_only1"
            group_var: "group_var_from_defaults_only1"
            group_var_all: "group_var_all_from_defaults_only1"
            extra_var: "extra_var_from_defaults_only1"
            """,
            '/etc/ansible/roles/defaults_only1/tasks/main.yml': """
            - debug: msg="here i am"
            """,

            # role defaults_only2
            '/etc/ansible/roles/defaults_only2/defaults/main.yml': """
            default_var: "default_var_from_defaults_only2"
            host_var: "host_var_from_defaults_only2"
            group_var: "group_var_from_defaults_only2"
            group_var_all: "group_var_all_from_defaults_only2"
            extra_var: "extra_var_from_defaults_only2"
            """,
        })

        mock_basedir.return_value = './'
        inv1 = Inventory(loader=fake_loader, variable_manager=v, host_list='/etc/ansible/inventory1')
        inv1.set_playbook_basedir('./')

        play1 = Play.load(dict(
           hosts=['all'],
           roles=['defaults_only1', 'defaults_only2'],
        ), loader=fake_loader, variable_manager=v)

        # first we assert that the defaults as viewed as a whole are the merged results
        # of the defaults from each role, with the last role defined "winning" when
        # there is a variable naming conflict
        res = v.get_vars(loader=fake_loader, play=play1)
        self.assertEqual(res['default_var'], 'default_var_from_defaults_only2')

        # next, we assert that when vars are viewed from the context of a task within a
        # role, that task will see its own role defaults before any other role's
        blocks = play1.compile()
        task = blocks[1].block[0]
        res = v.get_vars(loader=fake_loader, play=play1, task=task)
        self.assertEqual(res['default_var'], 'default_var_from_defaults_only1')

        # next we assert the precendence of inventory variables
        v.set_inventory(inv1)
        h1 = inv1.get_host('host1')

        res = v.get_vars(loader=fake_loader, play=play1, host=h1)
        self.assertEqual(res['group_var'], 'group_var_from_inventory_group1')
        self.assertEqual(res['host_var'], 'host_var_from_inventory_host1')

        # next we test with group_vars/ files loaded
        fake_loader.push("/etc/ansible/group_vars/all", """
        group_var_all: group_var_all_from_group_vars_all
        """)
        fake_loader.push("/etc/ansible/group_vars/group1", """
        group_var: group_var_from_group_vars_group1
        """)
        fake_loader.push("/etc/ansible/group_vars/group3", """
        # this is a dummy, which should not be used anywhere
        group_var: group_var_from_group_vars_group3
        """)
        fake_loader.push("/etc/ansible/host_vars/host1", """
        host_var: host_var_from_host_vars_host1
        """)

        v.add_group_vars_file("/etc/ansible/group_vars/all", loader=fake_loader)
        v.add_group_vars_file("/etc/ansible/group_vars/group1", loader=fake_loader)
        v.add_group_vars_file("/etc/ansible/group_vars/group2", loader=fake_loader)
        v.add_host_vars_file("/etc/ansible/host_vars/host1", loader=fake_loader)

        res = v.get_vars(loader=fake_loader, play=play1, host=h1)
        self.assertEqual(res['group_var'], 'group_var_from_group_vars_group1')
        self.assertEqual(res['group_var_all'], 'group_var_all_from_group_vars_all')
        self.assertEqual(res['host_var'], 'host_var_from_host_vars_host1')

        # add in the fact cache
        v._fact_cache['host1'] = dict(fact_cache_var="fact_cache_var_from_fact_cache")

        res = v.get_vars(loader=fake_loader, play=play1, host=h1)
        self.assertEqual(res['fact_cache_var'], 'fact_cache_var_from_fact_cache')

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

import os

from units.compat import unittest
from units.compat.mock import MagicMock, patch
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.six import iteritems
from ansible.playbook.play import Play


from units.mock.loader import DictDataLoader
from units.mock.path import mock_unfrackpath_noop

from ansible.vars.manager import VariableManager


class TestVariableManager(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_basic_manager(self):
        fake_loader = DictDataLoader({})

        mock_inventory = MagicMock()
        v = VariableManager(loader=fake_loader, inventory=mock_inventory)
        variables = v.get_vars(use_cache=False)

        # Check var manager expected values,  never check: ['omit', 'vars']
        # FIXME:  add the following ['ansible_version', 'ansible_playbook_python', 'groups']
        for varname, value in (('playbook_dir', os.path.abspath('.')), ):
            self.assertEqual(variables[varname], value)

    def test_variable_manager_extra_vars(self):
        fake_loader = DictDataLoader({})

        extra_vars = dict(a=1, b=2, c=3)
        mock_inventory = MagicMock()
        v = VariableManager(loader=fake_loader, inventory=mock_inventory)

        # override internal extra_vars loading
        v._extra_vars = extra_vars

        myvars = v.get_vars(use_cache=False)
        for (key, val) in iteritems(extra_vars):
            self.assertEqual(myvars.get(key), val)

    def test_variable_manager_options_vars(self):
        fake_loader = DictDataLoader({})

        options_vars = dict(a=1, b=2, c=3)
        mock_inventory = MagicMock()
        v = VariableManager(loader=fake_loader, inventory=mock_inventory)

        # override internal options_vars loading
        v._extra_vars = options_vars

        myvars = v.get_vars(use_cache=False)
        for (key, val) in iteritems(options_vars):
            self.assertEqual(myvars.get(key), val)

    def test_variable_manager_play_vars(self):
        fake_loader = DictDataLoader({})

        mock_play = MagicMock()
        mock_play.get_vars.return_value = dict(foo="bar")
        mock_play.get_roles.return_value = []
        mock_play.get_vars_files.return_value = []

        mock_inventory = MagicMock()
        v = VariableManager(loader=fake_loader, inventory=mock_inventory)
        self.assertEqual(v.get_vars(play=mock_play, use_cache=False).get("foo"), "bar")

    def test_variable_manager_play_vars_files(self):
        fake_loader = DictDataLoader({
            __file__: """
               foo: bar
            """
        })

        mock_play = MagicMock()
        mock_play.get_vars.return_value = dict()
        mock_play.get_roles.return_value = []
        mock_play.get_vars_files.return_value = [__file__]

        mock_inventory = MagicMock()
        v = VariableManager(inventory=mock_inventory, loader=fake_loader)
        self.assertEqual(v.get_vars(play=mock_play, use_cache=False).get("foo"), "bar")

    def test_variable_manager_task_vars(self):
        # FIXME: BCS make this work
        return

        # pylint: disable=unreachable
        fake_loader = DictDataLoader({})

        mock_task = MagicMock()
        mock_task._role = None
        mock_task.loop = None
        mock_task.get_vars.return_value = dict(foo="bar")
        mock_task.get_include_params.return_value = dict()

        mock_all = MagicMock()
        mock_all.get_vars.return_value = {}
        mock_all.get_file_vars.return_value = {}

        mock_host = MagicMock()
        mock_host.get.name.return_value = 'test01'
        mock_host.get_vars.return_value = {}
        mock_host.get_host_vars.return_value = {}

        mock_inventory = MagicMock()
        mock_inventory.hosts.get.return_value = mock_host
        mock_inventory.hosts.get.name.return_value = 'test01'
        mock_inventory.get_host.return_value = mock_host
        mock_inventory.groups.__getitem__.return_value = mock_all

        v = VariableManager(loader=fake_loader, inventory=mock_inventory)
        self.assertEqual(v.get_vars(task=mock_task, use_cache=False).get("foo"), "bar")

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_variable_manager_precedence(self):
        # FIXME: this needs to be redone as dataloader is not the automatic source of data anymore
        return

        # pylint: disable=unreachable
        '''
        Tests complex variations and combinations of get_vars() with different
        objects to modify the context under which variables are merged.
        '''
        # FIXME: BCS makethiswork
        # return True

        mock_inventory = MagicMock()

        inventory1_filedata = """
            [group2:children]
            group1

            [group1]
            host1 host_var=host_var_from_inventory_host1

            [group1:vars]
            group_var = group_var_from_inventory_group1

            [group2:vars]
            group_var = group_var_from_inventory_group2
            """

        fake_loader = DictDataLoader({
            # inventory1
            '/etc/ansible/inventory1': inventory1_filedata,
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

        inv1 = InventoryManager(loader=fake_loader, sources=['/etc/ansible/inventory1'])
        v = VariableManager(inventory=mock_inventory, loader=fake_loader)

        play1 = Play.load(dict(
            hosts=['all'],
            roles=['defaults_only1', 'defaults_only2'],
        ), loader=fake_loader, variable_manager=v)

        # first we assert that the defaults as viewed as a whole are the merged results
        # of the defaults from each role, with the last role defined "winning" when
        # there is a variable naming conflict
        res = v.get_vars(play=play1)
        self.assertEqual(res['default_var'], 'default_var_from_defaults_only2')

        # next, we assert that when vars are viewed from the context of a task within a
        # role, that task will see its own role defaults before any other role's
        blocks = play1.compile()
        task = blocks[1].block[0]
        res = v.get_vars(play=play1, task=task)
        self.assertEqual(res['default_var'], 'default_var_from_defaults_only1')

        # next we assert the precedence of inventory variables
        v.set_inventory(inv1)
        h1 = inv1.get_host('host1')

        res = v.get_vars(play=play1, host=h1)
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
        fake_loader.push("group_vars/group1", """
        playbook_group_var: playbook_group_var
        """)
        fake_loader.push("host_vars/host1", """
        playbook_host_var: playbook_host_var
        """)

        res = v.get_vars(play=play1, host=h1)
        # self.assertEqual(res['group_var'], 'group_var_from_group_vars_group1')
        # self.assertEqual(res['group_var_all'], 'group_var_all_from_group_vars_all')
        # self.assertEqual(res['playbook_group_var'], 'playbook_group_var')
        # self.assertEqual(res['host_var'], 'host_var_from_host_vars_host1')
        # self.assertEqual(res['playbook_host_var'], 'playbook_host_var')

        # add in the fact cache
        v._fact_cache['host1'] = dict(fact_cache_var="fact_cache_var_from_fact_cache")

        res = v.get_vars(play=play1, host=h1)
        self.assertEqual(res['fact_cache_var'], 'fact_cache_var_from_fact_cache')

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_variable_manager_role_vars_dependencies(self):
        '''
        Tests vars from role dependencies with duplicate dependencies.
        '''
        mock_inventory = MagicMock()

        fake_loader = DictDataLoader({
            # role common-role
            '/etc/ansible/roles/common-role/tasks/main.yml': """
            - debug: msg="{{role_var}}"
            """,
            # We do not need allow_duplicates: yes for this role
            # because eliminating duplicates is done by the execution
            # strategy, which we do not test here.

            # role role1
            '/etc/ansible/roles/role1/vars/main.yml': """
            role_var: "role_var_from_role1"
            """,
            '/etc/ansible/roles/role1/meta/main.yml': """
            dependencies:
              - { role: common-role }
            """,

            # role role2
            '/etc/ansible/roles/role2/vars/main.yml': """
            role_var: "role_var_from_role2"
            """,
            '/etc/ansible/roles/role2/meta/main.yml': """
            dependencies:
              - { role: common-role }
            """,
        })

        v = VariableManager(loader=fake_loader, inventory=mock_inventory)

        play1 = Play.load(dict(
            hosts=['all'],
            roles=['role1', 'role2'],
        ), loader=fake_loader, variable_manager=v)

        # The task defined by common-role exists twice because role1
        # and role2 depend on common-role.  Check that the tasks see
        # different values of role_var.
        blocks = play1.compile()
        task = blocks[1].block[0]
        res = v.get_vars(play=play1, task=task)
        self.assertEqual(res['role_var'], 'role_var_from_role1')

        task = blocks[2].block[0]
        res = v.get_vars(play=play1, task=task)
        self.assertEqual(res['role_var'], 'role_var_from_role2')

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

from __future__ import annotations

import os

import unittest
from unittest.mock import MagicMock, patch
from ansible.inventory.manager import InventoryManager
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.playbook.play import Play


from units.mock.loader import DictDataLoader
from units.mock.path import mock_unfrackpath_noop

from ansible.vars.manager import VariableManager


def _tag_ignore_magicmock():
    orig_tag = AnsibleTagHelper.tag
    return patch.object(AnsibleTagHelper, 'tag', lambda value, *args, **kwargs: value if isinstance(value, MagicMock) else orig_tag(value, *args, **kwargs))


class TestVariableManager(unittest.TestCase):

    def test_basic_manager(self):
        fake_loader = DictDataLoader({})

        mock_inventory = InventoryManager(loader=fake_loader)
        v = VariableManager(loader=fake_loader, inventory=mock_inventory)
        variables = v.get_vars(use_cache=False)

        # Check var manager expected values,  never check: ['omit', 'vars']
        # FIXME:  add the following ['ansible_version', 'ansible_playbook_python', 'groups']
        for varname, value in (('playbook_dir', os.path.abspath('.')), ):
            self.assertEqual(variables[varname], value)

    def test_variable_manager_extra_vars(self):
        fake_loader = DictDataLoader({})

        extra_vars = dict(a=1, b=2, c=3)
        mock_inventory = InventoryManager(loader=fake_loader)
        v = VariableManager(loader=fake_loader, inventory=mock_inventory)

        # override internal extra_vars loading
        v._extra_vars = extra_vars

        myvars = v.get_vars(use_cache=False)
        for key, val in extra_vars.items():
            self.assertEqual(myvars.get(key), val)

    def test_variable_manager_options_vars(self):
        fake_loader = DictDataLoader({})

        options_vars = dict(a=1, b=2, c=3)
        mock_inventory = InventoryManager(loader=fake_loader)
        v = VariableManager(loader=fake_loader, inventory=mock_inventory)

        # override internal options_vars loading
        v._extra_vars = options_vars

        myvars = v.get_vars(use_cache=False)
        for key, val in options_vars.items():
            self.assertEqual(myvars.get(key), val)

    def test_variable_manager_play_vars(self):
        fake_loader = DictDataLoader({})

        mock_play = MagicMock()
        mock_play.get_vars.return_value = dict(foo="bar")
        mock_play.get_roles.return_value = []
        mock_play.get_vars_files.return_value = []

        mock_inventory = MagicMock()

        v = VariableManager(loader=fake_loader, inventory=mock_inventory)

        with _tag_ignore_magicmock():
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
        with _tag_ignore_magicmock():
            self.assertEqual(v.get_vars(play=mock_play, use_cache=False).get("foo"), "bar")

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_variable_manager_role_vars_dependencies(self):
        """
        Tests vars from role dependencies with duplicate dependencies.
        """
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

        mock_inventory = InventoryManager(loader=fake_loader)

        with _tag_ignore_magicmock():
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

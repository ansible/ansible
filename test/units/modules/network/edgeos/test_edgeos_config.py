#
# (c) 2018 Red Hat Inc.
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

from units.compat.mock import patch
from ansible.modules.network.edgeos import edgeos_config
from units.modules.utils import set_module_args
from .edgeos_module import TestEdgeosModule, load_fixture


class TestEdgeosConfigModule(TestEdgeosModule):

    module = edgeos_config

    def setUp(self):
        super(TestEdgeosConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.edgeos.edgeos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.edgeos.edgeos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.edgeos.edgeos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestEdgeosConfigModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        config_file = 'edgeos_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_edgeos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_edgeos_config_unchanged_src(self):
        candidate_config = load_fixture('edgeos_config_config.cfg')
        set_module_args(dict(src=candidate_config))
        self.execute_module()

    def test_edgeos_config_unchanged_lines(self):
        candidate_config = [
            "set system host-name 'router'",
            "set system domain-name 'acme.com'",
            "set system domain-search domain 'acme.com'",
            "set system name-server 208.67.220.220",
            "set system name-server 208.67.222.222",
            "set interfaces ethernet eth0 address 1.2.3.4/24",
            "set interfaces ethernet eth0 description 'Outside'",
            "set interfaces ethernet eth1 address 10.77.88.1/24",
            "set interfaces ethernet eth1 description 'Inside'",
            "set interfaces ethernet eth1 disable"
        ]
        set_module_args(dict(lines=candidate_config))
        self.execute_module()

    def test_edgeos_config_changed_src(self):
        candidate_config = load_fixture('edgeos_config_src.cfg')
        set_module_args(dict(src=candidate_config))
        result_commands = [
            "delete interfaces ethernet eth0 address",
            "set system host-name er01",
        ]
        self.execute_module(changed=True, commands=result_commands)

    def test_edgeos_config_changed_src_brackets(self):
        candidate_config = load_fixture('edgeos_config_src_brackets.cfg')
        set_module_args(dict(src=candidate_config))
        result_commands = [
            "set interfaces ethernet eth0 address 10.10.10.10/24",
            "set system host-name er01"
        ]
        self.execute_module(changed=True, commands=result_commands)

    def test_edgeos_config_changed_lines(self):
        candidate_config = ["set system host-name test1"]
        set_module_args(dict(lines=candidate_config))
        result_updated = ["set system host-name test1"]
        self.execute_module(changed=True, commands=result_updated)

    def test_edgeos_config_changed_with_delete(self):
        candidate_config = [
            "delete interfaces ethernet eth0",
            "set interfaces ethernet eth0 address 1.2.3.4/24",
            "set interfaces ethernet eth0 description 'Outside'"
        ]
        set_module_args(dict(lines=candidate_config))
        result_updated = [
            "delete interfaces ethernet eth0",
            "set interfaces ethernet eth0 address 1.2.3.4/24",
            "set interfaces ethernet eth0 description 'Outside'"
        ]
        self.execute_module(changed=True, commands=result_updated)

    def test_edgeos_config_changed_delete_only(self):
        candidate_config = ["delete interfaces ethernet eth0"]
        set_module_args(dict(lines=candidate_config))
        result_updated = ["delete interfaces ethernet eth0"]
        self.execute_module(changed=True, commands=result_updated)

    def test_edgeos_config_config(self):
        config = ["set system host-name localhost"]
        candidate_config = ["set system host-name er01"]
        set_module_args(dict(lines=candidate_config, config=config))
        result_commands = ["set system host-name er01"]
        self.execute_module(changed=True, commands=result_commands)

    def test_edgeos_config_single_quote_wrapped_values(self):
        lines = ["set system interfaces ethernet eth0 description 'tests single quotes'"]
        set_module_args(dict(lines=lines))
        commands = ["set system interfaces ethernet eth0 description 'tests single quotes'"]
        self.execute_module(changed=True, commands=commands)

    def test_edgeos_config_single_quote_wrapped_values_failure(self):
        lines = ["set system interfaces ethernet eth0 description 'test's single quotes'"]
        set_module_args(dict(lines=lines))
        self.execute_module(failed=True)

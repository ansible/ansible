#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.asa import asa_acl
from units.modules.utils import set_module_args
from .asa_module import TestAsaModule, load_fixture


class TestAsaAclModule(TestAsaModule):
    module = asa_acl

    def setUp(self):
        super(TestAsaAclModule, self).setUp()

        self.mock_get_config = patch('ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.'
                                                         'get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.'
                                                        'get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch('ansible.module_utils.network.asa.providers.providers.CliProvider.edit_config')
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.asa.facts.acl.acl.'
                                               'AclFacts.get_acl_data')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestAsaAclModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        def load_from_file(*args, **kwargs):
            return load_fixture('asa_acl_config.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_asa_acl_merged(self):
        pass

    def test_asa_acl_merged_idempotent(self):
        pass

    def test_asa_acl_replaced(self):
        pass

    def test_asa_acl_replaced_idempotent(self):
        pass

    def test_asa_acl_overridden(self):
        pass

    def test_asa_acl_overridden_idempotent(self):
        pass
# -*- coding: utf-8 -*-

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.asa import asa_ogcontent
from units.modules.utils import set_module_args
from .asa_module import TestAsaModule, load_fixture


class TestAsaOgcontentModule(TestAsaModule):

    module = asa_ogcontent

    def setUp(self):
        super(TestAsaOgcontentModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.asa.asa_ogcontent.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_get_connection = patch('ansible.module_utils.network.asa.asa.get_connection')
        self.get_connection = self.mock_get_connection.start()

    def tearDown(self):
        super(TestAsaOgcontentModule, self).tearDown()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('asa_ogcontent_config.cfg').strip()

    def test_asa_og_idempotent(self):
        set_module_args(dict(
            name='aws_all_critical_vpcs'
        ))
        commands = ['show running-config object-group']
        self.execute_module(changed=False, commands=commands)

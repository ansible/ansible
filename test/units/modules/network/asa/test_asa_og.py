# -*- coding: utf-8 -*-

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.asa import asa_og
from units.modules.utils import set_module_args
from .asa_module import TestAsaModule, load_fixture


class TestAsaOgModule(TestAsaModule):

    module = asa_og

    def setUp(self):
        super(TestAsaOgModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.asa.asa_og.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.asa.asa_og.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_connection = patch('ansible.module_utils.network.asa.asa.get_connection')
        self.get_connection = self.mock_get_connection.start()

    def tearDown(self):
        super(TestAsaOgModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('asa_og_config.cfg').strip()
        self.load_config.return_value = dict(diff=None, session='session')

    def test_asa_og_idempotent(self):
        set_module_args(dict(
            name='test_nets',
            group_type='network-object',
            host_ip=['8.8.8.8'],
            ip_mask=['192.168.0.0 255.255.0.0'],
            group_object=['awx_lon'],
            description='ansible_test object-group description',
            state='present'
        ))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_asa_og_add(self):
        set_module_args(dict(
            name='test_nets',
            group_type='network-object',
            host_ip=['8.8.8.8', '8.8.4.4'],
            ip_mask=['192.168.0.0 255.255.0.0', '10.0.0.0 255.255.255.0'],
            group_object=['awx_lon', 'awx_ams'],
            description='ansible_test object-group description',
            state='present'
        ))
        commands = [
            'object-group network test_nets',
            'network-object host 8.8.4.4',
            'network-object 10.0.0.0 255.255.255.0',
            'group-object awx_ams'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_asa_og_replace(self):
        set_module_args(dict(
            name='test_nets',
            group_type='network-object',
            host_ip=['8.8.4.4'],
            ip_mask=['10.0.0.0 255.255.255.0'],
            group_object=['awx_ams'],
            description='ansible_test custom description',
            state='replace'
        ))
        commands = [
            'object-group network test_nets',
            'description ansible_test custom description',
            'no network-object host 8.8.8.8',
            'network-object host 8.8.4.4',
            'no network-object 192.168.0.0 255.255.0.0',
            'network-object 10.0.0.0 255.255.255.0',
            'no group-object awx_lon',
            'group-object awx_ams'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_asa_og_remove(self):
        set_module_args(dict(
            name='test_nets',
            group_type='network-object',
            host_ip=['8.8.8.8'],
            group_object=['awx_lon'],
            state='absent'
        ))
        commands = [
            'object-group network test_nets',
            'no network-object host 8.8.8.8',
            'no group-object awx_lon'
        ]
        self.execute_module(changed=True, commands=commands)

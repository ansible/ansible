#!/usr/bin/python
# -*- coding: utf-8 -*-

 # (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.frr.providers.cli.config.bgp import Provider
from ansible.modules.network.frr import frr_bgp
from .frr_module import TestFrrModule, load_fixture


class TestFrrBgpModule(TestFrrModule):
    module = frr_bgp

    def setUp(self):
        super(TestFrrBgpModule, self).setUp()
        self._bgp_config = load_fixture('frr_bgp_config')

    def test_frr_bgp(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, router_id='192.0.2.2'), operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['router bgp 64496', 'bgp router-id 192.0.2.2', 'exit'])

    def test_frr_bgp_idempotent(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, router_id='192.0.2.1'), operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_frr_bgp_remove(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496), operation='delete'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['no router bgp 64496'])

    def test_frr_bgp_neighbor(self):
        obj = Provider(params=dict(config=dict(bgp_as='64496', neighbors=[dict(neighbor='192.51.100.2', remote_as=64496)]),
                                   operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['router bgp 64496', 'neighbor 192.51.100.2 remote-as 64496', 'exit'])

    def test_frr_bgp_neighbor_idempotent(self):
        obj = Provider(params=dict(config=dict(bgp_as='64496', neighbors=[dict(neighbor='192.51.100.1', remote_as=64496,
                                                                               timers=dict(keepalive=120, holdtime=360))]),
                                   operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

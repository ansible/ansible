# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ingate Systems AB
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from units.compat.mock import patch
from ansible.modules.network.ingate import ig_config
from units.modules.utils import set_module_args
from .ingate_module import TestIngateModule, load_fixture


class TestConfigModule(TestIngateModule):

    module = ig_config

    def setUp(self):
        super(TestConfigModule, self).setUp()

        self.mock_make_request = patch('ansible.modules.network.ingate.'
                                       'ig_config.make_request')
        self.make_request = self.mock_make_request.start()
        # ATM the Ingate Python SDK is not needed in this unit test.
        self.module.HAS_INGATESDK = True

    def tearDown(self):
        super(TestConfigModule, self).tearDown()
        self.mock_make_request.stop()

    def load_fixtures(self, fixture=None, command=None, changed=False):
        self.make_request.side_effect = [(changed, command,
                                          load_fixture(fixture))]

    def test_ig_config_add(self):
        """Test adding a row to a table.
        """
        command = 'add'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            add=True,
            table='misc.dns_servers',
            columns=dict(
                server='192.168.1.23'
            )))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

    def test_ig_config_delete(self):
        """Test deleting all rows in a table.
        """
        command = 'delete'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            delete=True,
            table='misc.dns_servers',
        ))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

    def test_ig_config_get(self):
        """Test returning all rows in a table.
        """
        command = 'get'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            get=True,
            table='misc.dns_servers',
        ))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

    def test_ig_config_modify(self):
        """Test modifying a row.
        """
        command = 'modify'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            modify=True,
            table='misc.unitname',
            columns=dict(
                unitname='"Testapi - 1541699806"'
            )))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

    def test_ig_config_revert(self):
        """Test reverting the preliminary configuration.
        """
        command = 'revert'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            revert=True
        ))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

    def test_ig_config_factory(self):
        """Test loading factory defaults.
        """
        command = 'factory'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            factory=True
        ))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

    def test_ig_config_store(self):
        """Test storing the preliminary configuration.
        """
        command = 'store'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            store=True
        ))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

    def test_ig_config_download(self):
        """Test doing backup of configuration database.
        """
        command = 'store'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            download=True
        ))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

    def test_ig_config_return_rowid(self):
        """Test retrieving a row id.
        """
        command = 'return_rowid'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            return_rowid=True,
            table='network.local_nets',
            columns=dict(
                interface='eth0'
            )))
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(command in result)

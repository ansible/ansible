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
from ansible.modules.network.ingate import ig_system
from units.modules.utils import set_module_args
from .ingate_module import TestIngateModule, load_fixture


class TestSystemModule(TestIngateModule):

    module = ig_system

    def setUp(self):
        super(TestSystemModule, self).setUp()

        self.mock_make_request = patch('ansible.modules.network.ingate.'
                                       'ig_system.make_request')
        self.make_request = self.mock_make_request.start()
        # ATM the Ingate Python SDK is not needed in this unit test.
        self.module.HAS_INGATESDK = True

    def tearDown(self):
        super(TestSystemModule, self).tearDown()
        self.mock_make_request.stop()

    def load_fixtures(self, fixture=None, command=None, changed=False):
        self.make_request.side_effect = [(changed, command,
                                          load_fixture(fixture))]

    def test_ig_system_license(self):
        """Test installing a license.
        """
        command = 'license'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            license=True,
            username='myusername',
            password='mypassword',
            liccode='2STW-2UL8-JWJD')
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = ''
        try:
            data = result[command][1]['msg']
        except Exception:
            pass
        self.assertTrue('Install a Base license.' in data)

    def test_ig_system_patch(self):
        """Test installing a patch.
        """
        command = 'patch'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            patch=True,
            filename='patch-6.2.1-rc2-vm2')
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = result[command].get('msg', '')
        self.assertTrue('Installed the patch patch-6.2.1-rc2-vm2' in data)

    def test_ig_system_upgrade(self):
        """Test installing an upgrade.
        """
        command = 'upgrade'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            upgrade=True,
            filename='fupgrade.fup.any')
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = result[command].get('msg', '')
        self.assertTrue('Rebooting with new version' in data)

    def test_ig_system_upgrade_accept(self):
        """Test accepting an upgrade.
        """
        command = 'upgrade_accept'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            upgrade_accept=True)
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = result[command].get('msg', '')
        self.assertTrue('Made the upgrade permanent.' in data)

    def test_ig_system_upgrade_abort(self):
        """Test aborting an upgrade.
        """
        command = 'upgrade_abort'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            upgrade_abort=True)
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = result[command].get('msg', '')
        self.assertTrue('The upgrade has been removed. Rebooting...' in data)

    def test_ig_system_upgrade_downgrade(self):
        """Test downgrading an upgrade.
        """
        command = 'upgrade_downgrade'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            upgrade_downgrade=True)
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = result[command].get('msg', '')
        self.assertTrue('Downgrade in progress (6.2.0). Rebooting...' in data)

    def test_ig_system_upgrade_download(self):
        """Test upgrading to the latest version available.
        """
        command = 'upgrade_download'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            upgrade_download=True,
            username='myusername',
            password='mypassword',
            latest=True)
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = result[command].get('msg', '')
        self.assertTrue('upgraded to the latest version (6.2.2)' in data)

    def test_ig_system_reboot(self):
        """Test rebooting the unit.
        """
        command = 'reboot'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            reboot=True)
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = result[command].get('msg', '')
        self.assertTrue('Rebooting the unit now...' in data)

    def test_ig_system_opmode(self):
        """Test changing operational mode to Siparator.
        """
        command = 'opmode'
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            ),
            opmode=True,
            mode='siparator')
        )
        fixture = '%s_%s.%s' % (os.path.basename(__file__).split('.')[0],
                                command, 'json')
        result = self.execute_module(changed=True, fixture=fixture,
                                     command=command)
        self.assertTrue(result['changed'])
        self.assertTrue(command in result)
        data = result[command].get('msg', '')
        self.assertTrue('Operational mode set to siparator.' in data)

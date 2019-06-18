# (c) 2019 Red Hat Inc.
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
from ansible.modules.network.nxos import nxos_tms_global
from ansible.module_utils.network.nxos.nxos import NxosCmdRef
from .nxos_module import TestNxosModule, load_fixture, set_module_args

# TBD: These imports / import checks are only needed as a workaround for
# shippable, which fails this test due to import yaml & import ordereddict.
import pytest
from ansible.module_utils.network.nxos.nxos import nxosCmdRef_import_check
msg = nxosCmdRef_import_check()


@pytest.mark.skipif(len(msg), reason=msg)
class TestNxosTmsGlobalModule(TestNxosModule):

    module = nxos_tms_global

    def setUp(self):
        super(TestNxosTmsGlobalModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_tms_global.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.nxos.nxos.NxosCmdRef.execute_show_command')
        self.execute_show_command = self.mock_execute_show_command.start()

        self.mock_get_platform_shortname = patch('ansible.module_utils.network.nxos.nxos.NxosCmdRef.get_platform_shortname')
        self.get_platform_shortname = self.mock_get_platform_shortname.start()

    def tearDown(self):
        super(TestNxosTmsGlobalModule, self).tearDown()
        self.mock_load_config.stop()
        self.execute_show_command.stop()
        self.get_platform_shortname.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_tms_global_present_n9k(self):
        # Assumes feature telemetry is disabled
        # TMS global config is not present.
        self.execute_show_command.return_value = None
        set_module_args(dict(
            certificate={'key': '/bootflash/sample.key', 'hostname': 'server.example.com'},
            destination_profile_compression='gzip',
            destination_profile_source_interface='Ethernet2/1',
            destination_profile_vrf='blue',
        ))
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'certificate /bootflash/sample.key server.example.com',
            'destination-profile',
            'use-compression gzip',
            'source-interface Ethernet2/1',
            'use-vrf blue'
        ])

    def test_tms_global_present2_n9k(self):
        # Assumes feature telemetry is disabled
        # TMS global config is not present.
        # Configure only vrf
        module_name = self.module.__name__.rsplit('.', 1)[1]
        self.execute_show_command.return_value = None
        set_module_args(dict(
            destination_profile_vrf='blue',
        ))
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'destination-profile',
            'use-vrf blue'
        ])

    def test_tms_global_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            certificate={'key': '/bootflash/server.key', 'hostname': 'localhost'},
            destination_profile_compression='gzip',
            destination_profile_source_interface='loopback55',
            destination_profile_vrf='management',
        ))
        self.execute_module(changed=False)

    def test_tms_global_change_cert_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present
        # Change certificate
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            certificate={'key': '/bootflash/server.key', 'hostname': 'my_host'},
            destination_profile_compression='gzip',
            destination_profile_source_interface='loopback55',
            destination_profile_vrf='management',
        ))
        self.execute_module(changed=True, commands=[
            'telemetry',
            'certificate /bootflash/server.key my_host'
        ])

    def test_tms_global_change_interface_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present
        # Change interface
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            certificate={'key': '/bootflash/server.key', 'hostname': 'localhost'},
            destination_profile_compression='gzip',
            destination_profile_source_interface='Ethernet8/1',
            destination_profile_vrf='management',
        ))
        self.execute_module(changed=True, commands=[
            'telemetry',
            'destination-profile',
            'source-interface Ethernet8/1'
        ])

    def test_tms_global_change_several_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present
        # Change interface, vrf and cert
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            certificate={'key': '/bootflash/server_5.key', 'hostname': 'my_host'},
            destination_profile_compression='gzip',
            destination_profile_source_interface='Ethernet8/1',
            destination_profile_vrf='blue',
        ))
        self.execute_module(changed=True, commands=[
            'telemetry',
            'certificate /bootflash/server_5.key my_host',
            'destination-profile',
            'source-interface Ethernet8/1',
            'use-vrf blue',
        ])

    def test_tms_global_absent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        # Make absent with all playbook keys provided
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            state='absent',
            certificate={'key': '/bootflash/server.key', 'hostname': 'localhost'},
            destination_profile_compression='gzip',
            destination_profile_source_interface='loopback55',
            destination_profile_vrf='management',
        ))
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no certificate /bootflash/server.key localhost',
            'destination-profile',
            'no use-compression gzip',
            'no source-interface loopback55',
            'no use-vrf management'
        ])

    def test_tms_global_absent_certificate_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        # Make absent with only certificate key provided
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            state='absent',
            certificate={'key': '/bootflash/server.key', 'hostname': 'localhost'},
        ))
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no certificate /bootflash/server.key localhost',
        ])

    def test_tms_global_absent_vrf_int_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        # Make absent with only vrf and int keys provided
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            state='absent',
            destination_profile_source_interface='loopback55',
            destination_profile_vrf='management',
        ))
        self.execute_module(changed=True, commands=[
            'telemetry',
            'destination-profile',
            'no source-interface loopback55',
            'no use-vrf management'
        ])

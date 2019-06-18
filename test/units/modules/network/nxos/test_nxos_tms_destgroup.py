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
from units.modules.utils import AnsibleFailJson
from ansible.modules.network.nxos import nxos_tms_destgroup
from ansible.module_utils.network.nxos.nxos import NxosCmdRef
from .nxos_module import TestNxosModule, load_fixture, set_module_args

# TBD: These imports / import checks are only needed as a workaround for
# shippable, which fails this test due to import yaml & import ordereddict.
import pytest
from ansible.module_utils.network.nxos.nxos import nxosCmdRef_import_check
msg = nxosCmdRef_import_check()


@pytest.mark.skipif(len(msg), reason=msg)
class TestNxosTmsDestGroupModule(TestNxosModule):

    module = nxos_tms_destgroup

    def setUp(self):
        super(TestNxosTmsDestGroupModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_tms_destgroup.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.nxos.nxos.NxosCmdRef.execute_show_command')
        self.execute_show_command = self.mock_execute_show_command.start()

        self.mock_get_platform_shortname = patch('ansible.module_utils.network.nxos.nxos.NxosCmdRef.get_platform_shortname')
        self.get_platform_shortname = self.mock_get_platform_shortname.start()

    def tearDown(self):
        super(TestNxosTmsDestGroupModule, self).tearDown()
        self.mock_load_config.stop()
        self.execute_show_command.stop()
        self.get_platform_shortname.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_tms_destgroup_input_validation_1(self):
        # Mandatory parameter 'identifier' missing.
        self.execute_show_command.return_value = None
        set_module_args(dict(
            destination={'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
        ))
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        assert 'parameter: identifier is required' in str(errinfo.value[0]['msg'])
        assert errinfo.value[0]['failed']

    def test_tms_destgroup_input_validation_2(self):
        # Parameter 'aggregate' sub-parameter 'destination' is not a dict.
        self.execute_show_command.return_value = None
        set_module_args(dict(
            aggregate=[{'identifier': '28', 'destination': '192.168.1.1'}],
        ))
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        assert "parameter 'destination' must be a dict" in str(errinfo.value[0]['msg'])
        assert errinfo.value[0]['failed']

    def test_tms_destgroup_input_validation_3(self):
        # Parameter 'aggregate' sub-parameter 'destination' is not a dict.
        self.execute_show_command.return_value = None
        set_module_args(dict(
            aggregate=[{'identifier': '28', 'ip': '192.168.1.1', 'port': '5001'}],
        ))
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        assert 'contains unrecognized parameters' in str(errinfo.value[0]['msg'])
        assert errinfo.value[0]['failed']

    def test_tms_destgroup_input_validation_4(self):
        # Parameter 'aggregate' sub-parameter 'identifier' is required.
        self.execute_show_command.return_value = None
        set_module_args(dict(
            aggregate=[{'destination': 'foo'}],
        ))
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        assert "is missing required 'identifier' parameter" in str(errinfo.value[0]['msg'])
        assert errinfo.value[0]['failed']

    def test_tms_destgroup_present_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        self.execute_show_command.return_value = None
        set_module_args(dict(
            identifier='88',
            destination={'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
        ))
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'destination-group 88',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb'
        ])

    def test_tms_destgroup_present2_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        # Configure only identifier
        self.execute_show_command.return_value = None
        set_module_args(dict(
            identifier='88',
        ))
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'destination-group 88',
        ])

    def test_tms_destgroup_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        # Configure only identifier
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            identifier='2',
            destination={'ip': '192.168.0.2', 'port': '60001', 'protocol': 'grpc', 'encoding': 'gpb'},
        ))
        self.execute_module(changed=False)

    def test_tms_destgroup_idempotent2_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        # Configure only identifier
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            identifier='2',
        ))
        self.execute_module(changed=False)

    def test_tms_destgroup_present_aggregate_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        self.execute_show_command.return_value = None
        set_module_args(dict(
            aggregate=[{'identifier': '28',
                        'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'}
                        },
                       {'identifier': '35',
                        'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'}
                        }],
        ))
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'destination-group 28',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb',
            'feature telemetry',
            'telemetry',
            'destination-group 35',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb'
        ])

    def test_tms_destgroup_idempotent_aggregate_n9k(self):
        # TMS destgroup config is present.
        self.execute_show_command.return_value = load_fixture('nxos_tms', 'N9K.cfg')
        set_module_args(dict(
            # ip address 192.168.0.1 port 50001 protocol gRPC encoding GPB
            aggregate=[{'identifier': '2',
                        'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
                        },
                       {'identifier': '10',
                        'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
                        }],
        ))
        self.execute_module(changed=False)

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
from ansible.modules.network.nxos import nxos_telemetry
from ansible.module_utils.network.nxos.nxos import NxosCmdRef
from ansible.module_utils.network.nxos.config.telemetry.telemetry import Telemetry
from .nxos_module import TestNxosModule, load_fixture, set_module_args

# TBD: These imports / import checks are only needed as a workaround for
# shippable, which fails this test due to import yaml & import ordereddict.
import pytest
from ansible.module_utils.network.nxos.nxos import nxosCmdRef_import_check
msg = nxosCmdRef_import_check()
ignore_provider_arg = True


@pytest.mark.skipif(len(msg), reason=msg)
class TestNxosTelemetryModule(TestNxosModule):

    module = nxos_telemetry

    def setUp(self):
        super(TestNxosTelemetryModule, self).setUp()

        self.mock_FACT_LEGACY_SUBSETS = patch('ansible.module_utils.network.nxos.facts.facts.FACT_LEGACY_SUBSETS')
        self.FACT_LEGACY_SUBSETS = self.mock_FACT_LEGACY_SUBSETS.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch('ansible.module_utils.network.nxos.config.telemetry.telemetry.Telemetry.edit_config')
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.nxos.nxos.NxosCmdRef.execute_show_command')
        self.execute_show_command = self.mock_execute_show_command.start()

        self.mock_get_platform_shortname = patch('ansible.module_utils.network.nxos.nxos.NxosCmdRef.get_platform_shortname')
        self.get_platform_shortname = self.mock_get_platform_shortname.start()

    def tearDown(self):
        super(TestNxosTelemetryModule, self).tearDown()
        self.mock_FACT_LEGACY_SUBSETS.stop()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_execute_show_command.stop()
        self.get_platform_shortname.stop()

    def load_fixtures(self, commands=None, device=''):
        self.mock_FACT_LEGACY_SUBSETS.return_value = dict()
        self.get_resource_connection_config.return_value = 'Connection'
        self.get_resource_connection_facts.return_value = 'Connection'
        self.edit_config.return_value = None

    # ---------------------------
    # Telemetry Global Test Cases
    # ---------------------------

    def test_tms_global_merged_n9k(self):
        # Assumes feature telemetry is disabled
        # TMS global config is not present.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            config=dict(
                certificate={'key': '/bootflash/sample.key', 'hostname': 'server.example.com'},
                compression='gzip',
                source_interface='Ethernet2/1',
                vrf='blue',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'certificate /bootflash/sample.key server.example.com',
            'destination-profile',
            'use-compression gzip',
            'source-interface Ethernet2/1',
            'use-vrf blue'
        ])

    def test_tms_global_checkmode_n9k(self):
        # Assumes feature telemetry is disabled
        # TMS global config is not present.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            _ansible_check_mode=True,
            config=dict(
                certificate={'key': '/bootflash/sample.key', 'hostname': 'server.example.com'},
                compression='gzip',
                source_interface='Ethernet2/1',
                vrf='blue',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'certificate /bootflash/sample.key server.example.com',
            'destination-profile',
            'use-compression gzip',
            'source-interface Ethernet2/1',
            'use-vrf blue'
        ])

    def test_tms_global_merged2_n9k(self):
        # Assumes feature telemetry is disabled
        # TMS global config is not present.
        # Configure only vrf
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            config=dict(
                vrf='blue',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'destination-profile',
            'use-vrf blue'
        ])

    def test_tms_global_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            config=dict(
                certificate={'key': '/bootflash/server.key', 'hostname': 'localhost'},
                compression='gzip',
                source_interface='loopback55',
                vrf='management',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_global_change_cert_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present
        # Change certificate
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            config=dict(
                certificate={'key': '/bootflash/server.key', 'hostname': 'my_host'},
                compression='gzip',
                source_interface='loopback55',
                vrf='management',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'certificate /bootflash/server.key my_host'
        ])

    def test_tms_global_change_interface_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present
        # Change interface
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            config=dict(
                certificate={'key': '/bootflash/server.key', 'hostname': 'localhost'},
                compression='gzip',
                source_interface='Ethernet8/1',
                vrf='management',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'destination-profile',
            'source-interface Ethernet8/1'
        ])

    def test_tms_global_change_several_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present
        # Change source_interface, vrf and cert
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            config=dict(
                certificate={'key': '/bootflash/server_5.key', 'hostname': 'my_host'},
                compression='gzip',
                source_interface='Ethernet8/1',
                vrf='blue',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'certificate /bootflash/server_5.key my_host',
            'destination-profile',
            'source-interface Ethernet8/1',
            'use-vrf blue',
        ])

    # ------------------------------
    # Telemetry DestGroup Test Cases
    # ------------------------------

    def test_tms_destgroup_input_validation_1(self):
        # Mandatory parameter 'id' missing.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'}}
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Parameter <id> under <destination_groups> is required' in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_destgroup_input_validation_2(self):
        # Parameter 'destination' is not a dict.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '88',
             'destination': '192.168.1.1',
             }
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert "Parameter <destination> under <destination_groups> must be a dict" in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_destgroup_input_validation_3(self):
        # Parameter 'destination' is not a dict.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '88',
             'ip': '192.168.1.1',
             'port': '5001'
             }
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Playbook entry contains unrecongnized parameters' in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_destgroup_merged_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '88',
             'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
             },
            {'id': '88',
             'destination': {'ip': '192.168.1.2', 'port': '6001', 'protocol': 'GRPC', 'encoding': 'GPB'},
             },
            {'id': '99',
             'destination': {'ip': '192.168.1.2', 'port': '6001', 'protocol': 'GRPC', 'encoding': 'GPB'},
             },
            {'id': '99',
             'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
             },
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'destination-group 88',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb',
            'ip address 192.168.1.2 port 6001 protocol grpc encoding gpb',
            'destination-group 99',
            'ip address 192.168.1.2 port 6001 protocol grpc encoding gpb',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb',
        ])

    def test_tms_destgroup_checkmode_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '88',
             'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
             }
        ], 'destination_groups', state='merged', check_mode=True)
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'destination-group 88',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb'
        ])

    def test_tms_destgroup_merged2_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        # Configure only identifier
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '88'}
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'destination-group 88',
        ])

    def test_tms_destgroup_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        # Configure only identifier
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '2',
             'destination': {'ip': '192.168.0.2', 'port': '60001', 'protocol': 'grpc', 'encoding': 'gpb'},
             }
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_destgroup_idempotent2_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        # Configure only identifier
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '2'}
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_destgroup_merged_aggregate_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is present.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '2',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             },
            {'id': '10',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             }
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_destgroup_change_n9k(self):
        # TMS destgroup config is not present.
        # Change protocol and encoding for dest group 2
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '2',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'http', 'encoding': 'JSON'}
             },
            {'id': '10',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             }
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry', 'destination-group 2',
            'ip address 192.168.0.1 port 50001 protocol http encoding json'
        ])

    def test_tms_destgroup_add_n9k(self):
        # TMS destgroup config is not present.
        # Add destinations to destgroup 10
        # Add new destgroup 55 and 56
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '10',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             },
            {'id': '10',
             'destination': {'ip': '192.168.0.10', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             },
            {'id': '55',
             'destination': {'ip': '192.168.0.2', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             },
            {'id': '56'},
        ], 'destination_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'destination-group 10',
            'ip address 192.168.0.10 port 50001 protocol grpc encoding gpb',
            'destination-group 55',
            'ip address 192.168.0.2 port 50001 protocol grpc encoding gpb',
            'destination-group 56'
        ])

    # --------------------------------
    # Telemetry SensorGroup Test Cases
    # --------------------------------

    def test_tms_sensorgroup_merged_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS sensorgroup config is not present.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        td55_name = 'sys/bgp/inst/dom-default/peer-[10.10.10.11]/ent-[10.10.10.11]'
        td55_fc = 'or(eq(ethpmPhysIf.operSt,"down"),eq(ethpmPhysIf.operSt,"up"))'
        args = build_args([
            {'id': '2',
             'data_source': 'NX-API',
             'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'foo', 'filter_condition': 'foo'},
             },
            {'id': '2',
             'data_source': 'NX-API',
             'path': {'name': 'sys/bgp/inst', 'depth': 'unbounded', 'query_condition': 'foo', 'filter_condition': 'foo'},
             },
            {'id': '55',
             'data_source': 'DME',
             'path': {'name': td55_name, 'depth': 0, 'query_condition': 'foo', 'filter_condition': 'foo'},
             },
            {'id': '55',
             'data_source': 'DME',
             'path': {'name': 'sys/ospf', 'depth': 0, 'query_condition': 'foo', 'filter_condition': td55_fc},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 2',
            'data-source NX-API',
            'path sys/bgp depth 0 query-condition foo filter-condition foo',
            'path sys/bgp/inst depth unbounded query-condition foo filter-condition foo',
            'sensor-group 55',
            'data-source DME',
            'path sys/bgp/inst/dom-default/peer-[10.10.10.11]/ent-[10.10.10.11] depth 0 query-condition foo filter-condition foo',
            'path sys/ospf depth 0 query-condition foo filter-condition or(eq(ethpmPhysIf.operSt,"down"),eq(ethpmPhysIf.operSt,"up"))',
        ])

    def test_tms_sensorgroup_input_validation_1(self):
        # Mandatory parameter 'id' missing.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'data_source': 'DME',
             'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Parameter <id> under <sensor_groups> is required' in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_sensorgroup_input_validation_2(self):
        # Path present but mandatory 'name' key is not
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Parameter <path> under <sensor_groups> requires <name> key' in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_sensorgroup_resource_key_n9k(self):
        # TMS sensorgroup config is not present.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77'}
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
        ])

    def test_tms_sensorgroup_merged_variable_args1_n9k(self):
        # TMS sensorgroup config is not present.
        # Only path key name provided
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
            'data-source DME',
            'path sys/bgp',
        ])

    def test_tms_sensorgroup_merged_variable_args2_n9k(self):
        # TMS sensorgroup config is not present.
        # Only path keys name and depth provided
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp', 'depth': 0},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
            'data-source DME',
            'path sys/bgp depth 0',
        ])

    def test_tms_sensorgroup_merged_variable_args3_n9k(self):
        # TMS sensorgroup config is not present.
        # Only path keys name, depth and query_condition provided
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
            'data-source DME',
            'path sys/bgp depth 0 query-condition query_condition_xyz',
        ])

    def test_tms_sensorgroup_merged_variable_args4_n9k(self):
        # TMS sensorgroup config is not present.
        # Only path keys name, depth and filter_condition provided
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp', 'depth': 0, 'filter_condition': 'filter_condition_xyz'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
            'data-source DME',
            'path sys/bgp depth 0 filter-condition filter_condition_xyz',
        ])

    def test_tms_sensorgroup_merged_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS sensorgroup config is not present.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '2',
             'data_source': 'DME',
             'path': {'name': 'sys/ospf', 'depth': 0, 'query_condition': 'qc', 'filter_condition': 'fc'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_quotes_merged_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS sensorgroup config is present with quotes in NX-API path.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K_SGs.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '2',
             'data_source': 'NX-API',
             'path': {'name': '"show mac address-table count"', 'depth': 2},
             },
            {'id': '3',
             'data_source': 'NX-API',
             'path': {'name': '"show interface ethernet1/1-52"'},
             },
            {'id': '1',
             'path': {'name': 'sys/procsys', 'depth': 1},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_vxlan_idempotent_n9k(self):
        # TMS sensorgroup config present.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '56',
             'data_source': 'DME',
             'path': {'name': 'vxlan'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_idempotent_variable1_n9k(self):
        # TMS sensorgroup config is present with path key name.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '2',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp/inst/dom-default/peer-[10.10.10.11]/ent-[10.10.10.11]'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_idempotent_variable2_n9k(self):
        # TMS sensorgroup config is present with path key name and depth.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '2',
             'data_source': 'DME',
             'path': {'name': 'boo', 'depth': 0},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_idempotent_resource_key_n9k(self):
        # TMS sensorgroup config is present resource key only.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '55'}
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_present_path_environment_n9k(self):
        # TMS sensorgroup config is not present.
        # Path name 'environment' test
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77',
             'data_source': 'YANG',
             'path': {'name': 'environment'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
            'data-source YANG',
            'path environment',
        ])

    def test_tms_sensorgroup_present_path_interface_n9k(self):
        # TMS sensorgroup config is not present.
        # Path name 'interface' test
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77',
             'data_source': 'NATIVE',
             'path': {'name': 'interface'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
            'data-source NATIVE',
            'path interface',
        ])

    def test_tms_sensorgroup_present_path_interface_n9k(self):
        # TMS sensorgroup config is not present.
        # Path name 'resources' test
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': '77',
             'data_source': 'NX-API',
             'path': {'name': 'resources'},
             },
        ], 'sensor_groups')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
            'data-source NX-API',
            'path resources',
        ])

    # ---------------------------------
    # Telemetry Subscription Test Cases
    # ---------------------------------

    def test_tms_subscription_merged_n9k(self):
        # TMS subscription config is not present.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': 5,
             'destination_group': 55,
             'sensor_group': {'id': 1, 'sample_interval': 1000},
             },
            {'id': 88,
             'destination_group': 3,
             'sensor_group': {'id': 4, 'sample_interval': 2000},
             },
        ], 'subscriptions')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'subscription 5',
            'dst-grp 55',
            'snsr-grp 1 sample-interval 1000',
            'subscription 88',
            'dst-grp 3',
            'snsr-grp 4 sample-interval 2000'
        ])

    def test_tms_subscription_merged_idempotent_n9k(self):
        # TMS subscription config is not present.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': 3,
             },
            {'id': 7,
             'destination_group': 10,
             'sensor_group': {'id': 2, 'sample_interval': 1000},
             },
            {'id': 5,
             'destination_group': 2,
             'sensor_group': {'id': 2, 'sample_interval': 1000},
             },
        ], 'subscriptions')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_subscription_merged_change1_n9k(self):
        # TMS subscription config present.
        # Change sample interval for sensor group 2
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': 3,
             },
            {'id': 7,
             'destination_group': 10,
             'sensor_group': {'id': 2, 'sample_interval': 3000},
             },
            {'id': 5,
             'destination_group': 2,
             'sensor_group': {'id': 2, 'sample_interval': 1000},
             },
        ], 'subscriptions')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'subscription 7',
            'snsr-grp 2 sample-interval 3000'
        ])

    def test_tms_subscription_add_n9k(self):
        # TMS subscription config present.
        # Add new destination_group and sensor_group to subscription 5
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        args = build_args([
            {'id': 3,
             },
            {'id': 7,
             'destination_group': 10,
             'sensor_group': {'id': 2, 'sample_interval': 1000},
             },
            {'id': 5,
             'destination_group': 2,
             'sensor_group': {'id': 2, 'sample_interval': 1000},
             },
            {'id': 5,
             'destination_group': 7,
             'sensor_group': {'id': 2, 'sample_interval': 1000},
             },
            {'id': 5,
             'destination_group': 8,
             'sensor_group': {'id': 9, 'sample_interval': 1000},
             },
            {'id': 5,
             'destination_group': 9,
             'sensor_group': {'id': 10, 'sample_interval': 1000},
             },
        ], 'subscriptions')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'subscription 5',
            'dst-grp 7',
            'dst-grp 8',
            'dst-grp 9',
            'snsr-grp 9 sample-interval 1000',
            'snsr-grp 10 sample-interval 1000'
        ])

    def test_telemetry_full_n9k(self):
        # Assumes feature telemetry is disabled
        # TMS global config is not present.
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args({
            'state': 'merged',
            'config': {
                'certificate': {'key': '/bootflash/sample.key', 'hostname': 'server.example.com'},
                'compression': 'gzip',
                'source_interface': 'Ethernet2/1',
                'vrf': 'blue',
                'destination_groups': [
                    {'id': '88',
                     'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': '88',
                     'destination': {'ip': '192.168.1.2', 'port': '6001', 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': '99',
                     'destination': {'ip': '192.168.1.2', 'port': '6001', 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': '99',
                     'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                ],
                'sensor_groups': [
                    {'id': '77',
                     'data_source': 'DME',
                     'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
                     },
                    {'id': '99',
                     'data_source': 'DME',
                     'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
                     },
                ],
                'subscriptions': [
                    {'id': 5,
                     'destination_group': 88,
                     'sensor_group': {'id': 77, 'sample_interval': 1000},
                     },
                    {'id': 5,
                     'destination_group': 99,
                     'sensor_group': {'id': 77, 'sample_interval': 1000},
                     },
                    {'id': 88,
                     'destination_group': 99,
                     'sensor_group': {'id': 99, 'sample_interval': 2000},
                     },
                ],
            }
        }, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'certificate /bootflash/sample.key server.example.com',
            'destination-profile',
            'use-compression gzip',
            'source-interface Ethernet2/1',
            'use-vrf blue',
            'destination-group 88',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb',
            'ip address 192.168.1.2 port 6001 protocol grpc encoding gpb',
            'destination-group 99',
            'ip address 192.168.1.2 port 6001 protocol grpc encoding gpb',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb',
            'sensor-group 77',
            'data-source DME',
            'path sys/bgp depth 0 query-condition query_condition_xyz filter-condition filter_condition_xyz',
            'sensor-group 99',
            'data-source DME',
            'path sys/bgp depth 0 query-condition query_condition_xyz filter-condition filter_condition_xyz',
            'subscription 5',
            'dst-grp 88',
            'dst-grp 99',
            'snsr-grp 77 sample-interval 1000',
            'subscription 88',
            'dst-grp 99',
            'snsr-grp 99 sample-interval 2000'
        ])

    def test_telemetry_deleted_input_validation_n9k(self):
        # State is 'deleted' and 'config' key present.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            state='deleted',
            config=dict(
                certificate={'key': '/bootflash/server.key', 'hostname': 'localhost'},
                compression='gzip',
                source_interface='loopback55',
                vrf='management',
            )
        ), ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Remove config key from playbook when state is <deleted>' in str(testdata['msg'])
        assert testdata['failed']

    def test_telemetry_deleted_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        # Make absent with all playbook keys provided
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            state='deleted',
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=['no telemetry'])

    def test_telemetry_deleted_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        # Make absent with all playbook keys provided
        self.execute_show_command.return_value = None
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            state='deleted',
        ), ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_replaced1_n9k(self):
        # Assumes feature telemetry is enabled
        # Modify global config and remove everything else
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            state='replaced',
            config=dict(
                certificate={'key': '/bootflash/sample.key', 'hostname': 'server.example.com'},
                compression='gzip',
                vrf='blue',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no subscription 3',
            'no subscription 4',
            'no subscription 5',
            'no subscription 6',
            'no subscription 7',
            'no sensor-group 2',
            'no sensor-group 55',
            'no sensor-group 56',
            'no destination-group 2',
            'no destination-group 10',
            'certificate /bootflash/sample.key server.example.com',
            'destination-profile',
            'no source-interface loopback55',
            'use-vrf blue'
        ])

    def test_tms_replaced2_n9k(self):
        # Assumes feature telemetry is enabled
        # Remove/default all global config
        # Modify destination-group 10, add 11 and 99, remove 2
        # Modify sensor-group 55, 56
        # remove all subscriptions
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args({
            'state': 'replaced',
            'config': {
                'destination_groups': [
                    {'id': 10,
                     'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': 11,
                     'destination': {'ip': '192.168.1.2', 'port': '6001', 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': 99,
                     'destination': {'ip': '192.168.1.2', 'port': '6001', 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': '99',
                     'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                ],
                'sensor_groups': [
                    {'id': 55,
                     'data_source': 'NX-API',
                     'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
                     },
                    {'id': '56',
                     'data_source': 'NX-API',
                     'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
                     },
                ],
            }
        }, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no subscription 3',
            'no subscription 5',
            'no subscription 4',
            'no subscription 7',
            'no subscription 6',
            'sensor-group 56',
            'no data-source DME',
            'no path environment',
            'no path interface',
            'no path resources',
            'no path vxlan',
            'no sensor-group 2',
            'destination-group 10',
            'no ip address 192.168.0.1 port 50001 protocol grpc encoding gpb',
            'no ip address 192.168.0.2 port 60001 protocol grpc encoding gpb',
            'no destination-group 2',
            'destination-group 11',
            'ip address 192.168.1.2 port 6001 protocol grpc encoding gpb',
            'destination-group 10',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb',
            'destination-group 99',
            'ip address 192.168.1.2 port 6001 protocol grpc encoding gpb',
            'ip address 192.168.1.1 port 5001 protocol grpc encoding gpb',
            'sensor-group 55',
            'data-source NX-API',
            'path sys/bgp depth 0 query-condition query_condition_xyz filter-condition filter_condition_xyz',
            'sensor-group 56',
            'data-source NX-API',
            'path sys/bgp depth 0 query-condition query_condition_xyz filter-condition filter_condition_xyz',
            'no certificate /bootflash/server.key localhost',
            'no destination-profile'
        ])

    def test_tms_replaced3_n9k(self):
        # Assumes feature telemetry is enabled
        # Modify vrf global config, remove default all other global config.
        # destination-group 2 destination '192.168.0.1' idempotent
        # destination-group 2 destination '192.168.0.2' remove
        # remove all other destination-groups
        # Modify sensor-group 55 and delete all others
        # Modify subscription 7, add 10 and delete all others
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args({
            'state': 'replaced',
            'config': {
                'vrf': 'blue',
                'destination_groups': [
                    {'id': 2,
                     'destination': {'ip': '192.168.0.1', 'port': 50001, 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                ],
                'sensor_groups': [
                    {'id': 55,
                     'data_source': 'NX-API',
                     'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
                     },
                ],
                'subscriptions': [
                    {'id': 7,
                     'destination_group': 10,
                     'sensor_group': {'id': 55, 'sample_interval': 1000},
                     },
                    {'id': 10,
                     'destination_group': 2,
                     'sensor_group': {'id': 55, 'sample_interval': 1000},
                     },
                ],
            }
        }, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no subscription 3',
            'no subscription 5',
            'no subscription 4',
            'subscription 7',
            'no snsr-grp 2 sample-interval 1000',
            'no subscription 6',
            'no sensor-group 56',
            'no sensor-group 2',
            'no destination-group 10',
            'destination-group 2',
            'no ip address 192.168.0.2 port 60001 protocol grpc encoding gpb',
            'sensor-group 55',
            'data-source NX-API',
            'path sys/bgp depth 0 query-condition query_condition_xyz filter-condition filter_condition_xyz',
            'subscription 10',
            'dst-grp 2',
            'snsr-grp 55 sample-interval 1000',
            'subscription 7',
            'snsr-grp 55 sample-interval 1000',
            'no certificate /bootflash/server.key localhost',
            'destination-profile',
            'no use-compression gzip',
            'no source-interface loopback55',
            'use-vrf blue'
        ])

    def test_tms_replaced_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # Modify vrf global config, remove default all other global config.
        # destination-group 2 destination '192.168.0.1' idempotent
        # destination-group 2 destination '192.168.0.2' remove
        # remove all other destination-groups
        # Modify sensor-group 55 and delete all others
        # Modify subscription 7, add 10 and delete all others
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args({
            'state': 'replaced',
            'config': {
                'certificate': {'key': '/bootflash/server.key', 'hostname': 'localhost'},
                'compression': 'gzip',
                'vrf': 'management',
                'source_interface': 'loopback55',
                'destination_groups': [
                    {'id': 2,
                     'destination': {'ip': '192.168.0.1', 'port': 50001, 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': 2,
                     'destination': {'ip': '192.168.0.2', 'port': 60001, 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': 10,
                     'destination': {'ip': '192.168.0.1', 'port': 50001, 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                    {'id': 10,
                     'destination': {'ip': '192.168.0.2', 'port': 60001, 'protocol': 'GRPC', 'encoding': 'GPB'},
                     },
                ],
                'sensor_groups': [
                    {'id': 2,
                     'data_source': 'DME',
                     'path': {'name': 'boo', 'depth': 0},
                     },
                    {'id': 2,
                     'path': {'name': 'sys/ospf', 'depth': 0, 'query_condition': 'qc', 'filter_condition': 'fc'},
                     },
                    {'id': 2,
                     'path': {'name': 'interfaces', 'depth': 0},
                     },
                    {'id': 2,
                     'path': {'name': 'sys/bgp'},
                     },
                    {'id': 2,
                     'path': {'name': 'sys/bgp/inst', 'depth': 0, 'query_condition': 'foo', 'filter_condition': 'foo'},
                     },
                    {'id': 2,
                     'path': {'name': 'sys/bgp/inst/dom-default/peer-[10.10.10.11]/ent-[10.10.10.11]'},
                     },
                    {'id': 2,
                     'path': {'name': 'sys/bgp/inst/dom-default/peer-[20.20.20.11]/ent-[20.20.20.11]'},
                     },
                    {'id': 2,
                     'path': {'name': 'too', 'depth': 0, 'filter_condition': 'foo'},
                     },
                    {'id': 55},
                    {'id': 56,
                     'data_source': 'DME',
                     },
                    {'id': 56,
                     'path': {'name': 'environment'},
                     },
                    {'id': 56,
                     'path': {'name': 'interface'},
                     },
                    {'id': 56,
                     'path': {'name': 'resources'},
                     },
                    {'id': 56,
                     'path': {'name': 'vxlan'},
                     },
                ],
                'subscriptions': [
                    {'id': 3},
                    {'id': 4,
                     'destination_group': 2,
                     'sensor_group': {'id': 2, 'sample_interval': 1000},
                     },
                    {'id': 5,
                     'destination_group': 2,
                     },
                    {'id': 5,
                     'sensor_group': {'id': 2, 'sample_interval': 1000},
                     },
                    {'id': 6,
                     'destination_group': 10,
                     },
                    {'id': 7,
                     'destination_group': 10,
                     'sensor_group': {'id': 2, 'sample_interval': 1000},
                     },
                ],
            }
        }, ignore_provider_arg)
        self.execute_module(changed=False, commands=[])


def build_args(data, type, state=None, check_mode=None):
    if state is None:
        state = 'merged'
    if check_mode is None:
        check_mode = False
    args = {
        'state': state,
        '_ansible_check_mode': check_mode,
        'config': {
            type: data
        }
    }
    return args

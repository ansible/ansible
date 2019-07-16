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

    def test_tms_global_deleted_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        # Make absent with all playbook keys provided
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
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no certificate /bootflash/server.key localhost',
            'destination-profile',
            'no use-compression gzip',
            'no source-interface loopback55',
            'no use-vrf management'
        ])

    def test_tms_global_deleted_certificate_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        # Make absent with only certificate key provided
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            state='deleted',
            config=dict(
                certificate={'key': '/bootflash/server.key', 'hostname': 'localhost'},
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no certificate /bootflash/server.key localhost',
        ])

    def test_tms_global_deleted_vrf_int_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS global config is present.
        # Make absent with only vrf and int keys provided
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            state='deleted',
            config=dict(
                source_interface='loopback55',
                vrf='management',
            )
        ), ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'destination-profile',
            'no source-interface loopback55',
            'no use-vrf management'
        ])

    # ------------------------------
    # Telemetry DestGroup Test Cases
    # ------------------------------

    def test_tms_destgroup_input_validation_1(self):
        # Mandatory parameter 'id' missing.
        self.execute_show_command.return_value = None
        args = build_destgroup_args([
            {'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'}}
        ])
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Parameter <id> under <destination_groups> is required' in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_destgroup_input_validation_2(self):
        # Parameter 'destination' is not a dict.
        self.execute_show_command.return_value = None
        args = build_destgroup_args([
            {'id': '88',
             'destination': '192.168.1.1',
             }
        ])
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert "Parameter <destination> under <destination_groups> must be a dict" in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_destgroup_input_validation_3(self):
        # Parameter 'destination' is not a dict.
        self.execute_show_command.return_value = None
        args = build_destgroup_args([
            {'id': '88',
             'ip': '192.168.1.1',
             'port': '5001'
             }
        ])
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
        args = build_destgroup_args([
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
        ])
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
        args = build_destgroup_args([
            {'id': '88',
             'destination': {'ip': '192.168.1.1', 'port': '5001', 'protocol': 'GRPC', 'encoding': 'GPB'},
             }
        ], state='merged', check_mode=True)
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
        args = build_destgroup_args([
            {'id': '88'}
        ])
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
        args = build_destgroup_args([
            {'id': '2',
             'destination': {'ip': '192.168.0.2', 'port': '60001', 'protocol': 'grpc', 'encoding': 'gpb'},
             }
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_destgroup_idempotent2_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        # Configure only identifier
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_destgroup_args([
            {'id': '2'}
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_destgroup_merged_aggregate_idempotent_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS destgroup config is not present.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_destgroup_args([
            {'id': '2',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             },
            {'id': '10',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             }
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_destgroup_deleted_n9k(self):
        # Delete destination groups
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_destgroup_args([
            {'id': '2',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             },
            {'id': '10',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             }
        ], state='deleted')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no destination-group 2',
            'no destination-group 10'
        ])

    def test_tms_destgroup_deleted_idempotent_n9k(self):
        # Delete destination groups
        self.execute_show_command.return_value = None
        args = build_destgroup_args([
            {'id': '2',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             },
            {'id': '10',
             'destination': {'ip': '192.168.0.1', 'port': '50001', 'protocol': 'gRPC', 'encoding': 'gpb'}
             }
        ], state='deleted')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_destgroup_deleted2_n9k(self):
        # Delete destination groups only provide id in playbook
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_destgroup_args([
            {'id': '2'},
            {'id': '10'},
        ], state='deleted')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no destination-group 2',
            'no destination-group 10'
        ])

    # --------------------------------
    # Telemetry SensorGroup Test Cases
    # --------------------------------

    def test_tms_sensorgroup_merged_n9k(self):
        # Assumes feature telemetry is enabled
        # TMS sensorgroup config is not present.
        self.execute_show_command.return_value = None
        args = build_sensorgroup_args([
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
             'path': {'name': 'sys/bgp/inst/dom-default/peer-[10.10.10.11]/ent-[10.10.10.11]', 'depth': 0, 'query_condition': 'foo', 'filter_condition': 'foo'},
             },
            {'id': '55',
             'data_source': 'DME',
             'path': {'name': 'sys/ospf', 'depth': 0, 'query_condition': 'foo', 'filter_condition': 'or(eq(ethpmPhysIf.operSt,"down"),eq(ethpmPhysIf.operSt,"up"))'},
             },
        ])
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
        args = build_sensorgroup_args([
            {'data_source': 'DME',
             'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
             },
        ])
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Parameter <id> under <sensor_groups> is required' in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_sensorgroup_input_validation_2(self):
        # Path present but mandatory 'name' key is not
        self.execute_show_command.return_value = None
        args = build_sensorgroup_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'depth': 0, 'query_condition': 'query_condition_xyz', 'filter_condition': 'filter_condition_xyz'},
             },
        ])
        set_module_args(args, ignore_provider_arg)
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Parameter <path> under <sensor_groups> requires <name> key' in str(testdata['msg'])
        assert testdata['failed']

    def test_tms_sensorgroup_resource_key_n9k(self):
        # TMS sensorgroup config is not present.
        self.execute_show_command.return_value = None
        args = build_sensorgroup_args([
            {'id': '77'}
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
        ])

    # def test_tms_sensorgroup_resource_key2_n9k(self):
    #     # Feature telemetry is enabled
    #     # TMS sensorgroup config is not present.
    #     self.execute_show_command.side_effect = ['feature telemetry', []]
    #     args = build_sensorgroup_args([
    #         {'id': '77'}
    #     ])
    #     set_module_args(args)
    #     self.execute_module(changed=True, commands=[
    #         'telemetry',
    #         'sensor-group 77',
    #     ])

    def test_tms_sensorgroup_merged_variable_args1_n9k(self):
        # TMS sensorgroup config is not present.
        # Only path key name provided
        self.execute_show_command.return_value = None
        args = build_sensorgroup_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp'},
             },
        ])
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
        args = build_sensorgroup_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp', 'depth': 0},
             },
        ])
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
        args = build_sensorgroup_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp', 'depth': 0, 'query_condition': 'query_condition_xyz'},
             },
        ])
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
        args = build_sensorgroup_args([
            {'id': '77',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp', 'depth': 0, 'filter_condition': 'filter_condition_xyz'},
             },
        ])
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
        args = build_sensorgroup_args([
            {'id': '2',
             'data_source': 'DME',
             'path': {'name': 'sys/ospf', 'depth': 0, 'query_condition': 'qc', 'filter_condition': 'fc'},
             },
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_vxlan_idempotent_n9k(self):
        # TMS sensorgroup config present.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_sensorgroup_args([
            {'id': '56',
             'data_source': 'DME',
             'path': {'name': 'vxlan'},
             },
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_idempotent_variable1_n9k(self):
        # TMS sensorgroup config is present with path key name.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_sensorgroup_args([
            {'id': '2',
             'data_source': 'DME',
             'path': {'name': 'sys/bgp/inst/dom-default/peer-[10.10.10.11]/ent-[10.10.10.11]'},
             },
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_idempotent_variable2_n9k(self):
        # TMS sensorgroup config is present with path key name and depth.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_sensorgroup_args([
            {'id': '2',
             'data_source': 'DME',
             'path': {'name': 'boo', 'depth': 0},
             },
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_idempotent_resource_key_n9k(self):
        # TMS sensorgroup config is present resource key only.
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_sensorgroup_args([
            {'id': '55'}
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_tms_sensorgroup_deleted_n9k(self):
        # TMS sensorgroup config is present.
        # Make absent with all playbook keys provided
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_sensorgroup_args([
            {'id': '2',
             'data_source': 'DME',
             'path': {'name': 'sys/ospf', 'depth': 0, 'query_condition': 'qc', 'filter_condition': 'fc'},
             },
        ], state='deleted')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no sensor-group 2'
        ])

    def test_tms_sensorgroup_deleted2_n9k(self):
        # TMS sensorgroup config is present.
        # Make absent with only identifier playbook keys provided
        self.execute_show_command.return_value = load_fixture('nxos_telemetry', 'N9K.cfg')
        args = build_sensorgroup_args([
            {'id': '2'}
        ], state='deleted')
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'telemetry',
            'no sensor-group 2'
        ])

    def test_tms_sensorgroup_present_path_environment_n9k(self):
        # TMS sensorgroup config is not present.
        # Path name 'environment' test
        self.execute_show_command.return_value = None
        args = build_sensorgroup_args([
            {'id': '77',
             'data_source': 'YANG',
             'path': {'name': 'environment'},
             },
        ])
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
        args = build_sensorgroup_args([
            {'id': '77',
             'data_source': 'NATIVE',
             'path': {'name': 'interface'},
             },
        ])
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
        args = build_sensorgroup_args([
            {'id': '77',
             'data_source': 'NX-API',
             'path': {'name': 'resources'},
             },
        ])
        set_module_args(args, ignore_provider_arg)
        self.execute_module(changed=True, commands=[
            'feature telemetry',
            'telemetry',
            'sensor-group 77',
            'data-source NX-API',
            'path resources',
        ])

    def test_telemetry_full_n9k(self):
        # Assumes feature telemetry is disabled
        # TMS global config is not present.
        self.execute_show_command.return_value = None
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
        ])


def build_destgroup_args(data, state=None, check_mode=None):
    if state is None:
        state = 'merged'
    if check_mode is None:
        check_mode = False
    args = {
        'state': state,
        '_ansible_check_mode': check_mode,
        'config': {
            'destination_groups': data
        }
    }
    return args


def build_sensorgroup_args(data, state=None, check_mode=None):
    if state is None:
        state = 'merged'
    if check_mode is None:
        check_mode = False
    args = {
        'state': state,
        '_ansible_check_mode': check_mode,
        'config': {
            'sensor_groups': data
        }
    }
    return args

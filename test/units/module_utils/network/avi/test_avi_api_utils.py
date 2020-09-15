'''
Created on Aug 16, 2016

@author: grastogi
'''
import unittest
from ansible.module_utils.network.avi.ansible_utils import \
    cleanup_absent_fields, avi_obj_cmp


class TestAviApiUtils(unittest.TestCase):

    def test_avi_obj_cmp(self):
        obj = {'name': 'testpool'}
        existing_obj = {
            'lb_algorithm': 'LB_ALGORITHM_LEAST_CONNECTIONS',
            'use_service_port': False,
            'server_auto_scale': False,
            'host_check_enabled': False,
            'enabled': True,
            'capacity_estimation': False,
            'fewest_tasks_feedback_delay': 10,
            '_last_modified': '1471377748747040',
            'cloud_ref': 'https://192.0.2.42/api/cloud/cloud-afe8bf2c-9821-4272-9bc6-67634c84bec9',
            'vrf_ref': 'https://192.0.2.42/api/vrfcontext/vrfcontext-0e8ce760-fed2-4650-9397-5b3e4966376e',
            'inline_health_monitor': True,
            'default_server_port': 80,
            'request_queue_depth': 128,
            'graceful_disable_timeout': 1,
            'server_count': 0,
            'sni_enabled': True,
            'request_queue_enabled': False,
            'name': 'testpool',
            'max_concurrent_connections_per_server': 0,
            'url': 'https://192.0.2.42/api/pool/pool-20084ee1-872e-4103-98e1-899103e2242a',
            'tenant_ref': 'https://192.0.2.42/api/tenant/admin',
            'uuid': 'pool-20084ee1-872e-4103-98e1-899103e2242a',
            'connection_ramp_duration': 10}

        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

    def test_avi_obj_cmp_w_refs(self):
        obj = {'name': 'testpool',
               'health_monitor_refs': ['/api/healthmonitor?name=System-HTTP'],
               'enabled': True}
        existing_obj = {
            'lb_algorithm': 'LB_ALGORITHM_LEAST_CONNECTIONS',
            'use_service_port': False,
            'server_auto_scale': False,
            'host_check_enabled': False,
            'enabled': True,
            'capacity_estimation': False,
            'fewest_tasks_feedback_delay': 10,
            '_last_modified': '1471377748747040',
            'cloud_ref': 'https://192.0.2.42/api/cloud/cloud-afe8bf2c-9821-4272-9bc6-67634c84bec9',
            'vrf_ref': 'https://192.0.2.42/api/vrfcontext/vrfcontext-0e8ce760-fed2-4650-9397-5b3e4966376e',
            'inline_health_monitor': True,
            'default_server_port': 80,
            'request_queue_depth': 128,
            'graceful_disable_timeout': 1,
            'server_count': 0,
            'sni_enabled': True,
            'request_queue_enabled': False,
            'name': 'testpool',
            'max_concurrent_connections_per_server': 0,
            'url': 'https://192.0.2.42/api/pool/pool-20084ee1-872e-4103-98e1-899103e2242a',
            'tenant_ref': 'https://192.0.2.42/api/tenant/admin',
            'uuid': 'pool-20084ee1-872e-4103-98e1-899103e2242a',
            'connection_ramp_duration': 10,
            'health_monitor_refs': [
                "https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc9#System-HTTP"],
        }

        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

        obj = {'name': 'testpool',
               'health_monitor_refs': ['/api/healthmonitor?name=System-HTTP'],
               'server_count': 1}
        diff = avi_obj_cmp(obj, existing_obj)
        assert not diff

        obj = {'name': 'testpool',
               'health_monitor_refs': ['api/healthmonitor?name=System-HTTP'],
               'server_count': 0}
        diff = avi_obj_cmp(obj, existing_obj)
        assert not diff
        obj = {'name': 'testpool',
               'health_monitor_refs': ['healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc9'],
               'server_count': 0}
        diff = avi_obj_cmp(obj, existing_obj)
        assert diff
        obj = {'name': 'testpool#asdfasf',
               'health_monitor_refs': ['api/healthmonitor?name=System-HTTP'],
               'server_count': 0}
        diff = avi_obj_cmp(obj, existing_obj)
        assert not diff
        obj = {'name': 'testpool',
               'health_monitor_refs': ['/api/healthmonitor?name=System-HTTP#'],
               'server_count': 0}
        diff = avi_obj_cmp(obj, existing_obj)
        assert not diff

    def test_avi_obj_cmp_empty_list(self):
        obj = {'name': 'testpool',
               'health_monitor_refs': [],
               'enabled': True}
        existing_obj = {
            'lb_algorithm': 'LB_ALGORITHM_LEAST_CONNECTIONS',
            'use_service_port': False,
            'server_auto_scale': False,
            'host_check_enabled': False,
            'enabled': True,
            'capacity_estimation': False,
            'fewest_tasks_feedback_delay': 10,
            '_last_modified': '1471377748747040',
            'cloud_ref': 'https://192.0.2.42/api/cloud/cloud-afe8bf2c-9821-4272-9bc6-67634c84bec9',
            'vrf_ref': 'https://192.0.2.42/api/vrfcontext/vrfcontext-0e8ce760-fed2-4650-9397-5b3e4966376e',
            'inline_health_monitor': True,
            'default_server_port': 80,
            'request_queue_depth': 128,
            'graceful_disable_timeout': 1,
            'server_count': 0,
            'sni_enabled': True,
            'request_queue_enabled': False,
            'name': 'testpool',
            'max_concurrent_connections_per_server': 0,
            'url': 'https://192.0.2.42/api/pool/pool-20084ee1-872e-4103-98e1-899103e2242a',
            'tenant_ref': 'https://192.0.2.42/api/tenant/admin',
            'uuid': 'pool-20084ee1-872e-4103-98e1-899103e2242a',
            'connection_ramp_duration': 10
        }
        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

    def test_avi_obj_cmp_w_refs_n_name(self):
        existing_obj = {
            'use_service_port': False,
            'server_auto_scale': False,
            'host_check_enabled': False,
            'enabled': True,
            'capacity_estimation': False,
            'fewest_tasks_feedback_delay': 10,
            '_last_modified': '1471377748747040',
            'cloud_ref': 'https://192.0.2.42/api/cloud/cloud-afe8bf2c-9821-4272-9bc6-67634c84bec9',
            'vrf_ref': 'https://192.0.2.42/api/vrfcontext/vrfcontext-0e8ce760-fed2-4650-9397-5b3e4966376e',
            'inline_health_monitor': True,
            'default_server_port': 80,
            'request_queue_depth': 128,
            'graceful_disable_timeout': 1,
            'server_count': 0,
            'sni_enabled': True,
            'request_queue_enabled': False,
            'name': 'testpool',
            'max_concurrent_connections_per_server': 0,
            'url': 'https://192.0.2.42/api/pool/pool-20084ee1-872e-4103-98e1-899103e2242a',
            'tenant_ref': 'https://192.0.2.42/api/tenant/admin',
            'uuid': 'pool-20084ee1-872e-4103-98e1-899103e2242a',
            'connection_ramp_duration': 10,
            'health_monitor_refs': [
                "https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc9#System-HTTP",
                "https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc8",
            ],
        }

        obj = {'name': 'testpool',
               'health_monitor_refs': ['https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc9',
                                       "https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc8"],
               'server_count': 0}
        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

        obj = {'name': 'testpool',
               'health_monitor_refs': [
                   'https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc9#System-HTTP',
                   "https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc8"],
               'server_count': 0}
        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

        obj = {'name': 'testpool',
               'health_monitor_refs': [
                   'https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc9#System-HTTP',
                   "https://192.0.2.42/api/healthmonitor/healthmonitor-6d07b57f-126b-476c-baba-a8c8c8b06dc8#System-HTTP2"],
               'server_count': 0,
               'cloud_ref': 'https://192.0.2.42/api/cloud/cloud-afe8bf2c-9821-4272-9bc6-67634c84bec9#Default-Cloud',
               }
        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

    def test_avi_list_update(self):
        existing_obj = {
            'services': [
                {
                    "enable_ssl": False,
                    "port_range_end": 80,
                    "port": 80
                },
                {
                    "enable_ssl": False,
                    "port_range_end": 443,
                    "port": 443
                }
            ],
            "name": "vs-health-test",
            "url": "https://192.0.2.42/api/virtualservice/virtualservice-526c55c2-df89-40b9-9de6-e45a472290aa",
        }

        obj = {
            'services': [
                {
                    "enable_ssl": False,
                    "port_range_end": 80,
                    "port": 80
                }
            ]
        }

        diff = avi_obj_cmp(obj, existing_obj)
        assert not diff

        obj = {
            'services': [
                {
                    "enable_ssl": False,
                    "port_range_end": 80,
                    "port": 80
                },
                {
                    "enable_ssl": False,
                    "port_range_end": 443,
                    "port": 80
                }
            ],
            "name": "vs-health-test",
            "url": "https://192.0.2.42/api/virtualservice/virtualservice-526c55c2-df89-40b9-9de6-e45a472290aa",
        }

        diff = avi_obj_cmp(obj, existing_obj)
        assert not diff

    def test_cleanup_abset(self):
        obj = {'x': 10,
               'y': {'state': 'absent'},
               'z': {'a': {'state': 'absent'}},
               'l': [{'y1': {'state': 'absent'}}],
               'z1': {'a': {'state': 'absent'}, 'b': {}, 'c': 42},
               'empty': []}

        obj = cleanup_absent_fields(obj)

        assert 'y' not in obj
        assert 'z' not in obj
        assert 'l' not in obj
        assert 'z1' in obj
        assert 'b' not in obj['z1']
        assert 'a' not in obj['z1']
        assert 'empty' not in obj

    def test_complex_obj(self):

        obj = {
            'lb_algorithm': 'LB_ALGORITHM_ROUND_ROBIN',
            'use_service_port': False, 'server_auto_scale': False,
            'host_check_enabled': False,
            'tenant_ref': 'https://192.0.2.42/api/tenant/admin#admin',
            'capacity_estimation': False,
            'servers': [{
                'hostname': 'grastogi-server6', 'ratio': 1,
                'ip': {'type': 'V4', 'addr': '198.51.100.62'},
                'discovered_networks': [{
                    'subnet': [{
                        'ip_addr': {
                            'type': 'V4',
                            'addr': '198.51.100.0'
                        },
                        'mask': 24
                    }],
                    'network_ref': 'https://192.0.2.42/api/network/dvportgroup-53975-10.10.2.10#PG-964'
                }],
                'enabled': True, 'nw_ref': 'https://192.0.2.42/api/vimgrnwruntime/dvportgroup-53975-10.10.2.10#PG-964',
                'verify_network': False,
                'static': False,
                'resolve_server_by_dns': False,
                'external_uuid': 'vm-4230615e-bc0b-3d33-3929-1c7328575993',
                'vm_ref': 'https://192.0.2.42/api/vimgrvmruntime/vm-4230615e-bc0b-3d33-3929-1c7328575993#grastogi-server6'
            }, {
                'hostname': 'grastogi-server6',
                'ratio': 1,
                'ip': {
                    'type': 'V4',
                    'addr': '198.51.100.61'
                },
                'discovered_networks': [{
                    'subnet': [{
                        'ip_addr': {
                            'type': 'V4',
                            'addr': '198.51.100.0'
                        },
                        'mask': 24
                    }],
                    'network_ref': 'https://192.0.2.42/api/network/dvportgroup-53975-10.10.2.10#PG-964'
                }],
                'enabled': True,
                'nw_ref': 'https://192.0.2.42/api/vimgrnwruntime/dvportgroup-53975-10.10.2.10#PG-964',
                'verify_network': False,
                'static': False,
                'resolve_server_by_dns': False,
                'external_uuid': 'vm-4230615e-bc0b-3d33-3929-1c7328575993',
                'vm_ref': 'https://192.0.2.42/api/vimgrvmruntime/vm-4230615e-bc0b-3d33-3929-1c7328575993#grastogi-server6'
            }, {
                'hostname': 'grastogi-server6',
                'ratio': 1,
                'ip': {
                    'type': 'V4',
                    'addr': '198.51.100.65'
                },
                'discovered_networks': [{
                    'subnet': [{
                        'ip_addr': {
                            'type': 'V4',
                            'addr': '198.51.100.0'
                        }, 'mask': 24
                    }],
                    'network_ref': 'https://192.0.2.42/api/network/dvportgroup-53975-10.10.2.10#PG-964'
                }],
                'enabled': True,
                'verify_network': False,
                'static': False,
                'resolve_server_by_dns': False
            }],
            'fewest_tasks_feedback_delay': 10,
            '_last_modified': '1473292763246107',
            'cloud_ref': 'https://192.0.2.42/api/cloud/cloud-e0696a58-8b72-4026-923c-9a87c38a2489#Default-Cloud',
            'vrf_ref': 'https://192.0.2.42/api/vrfcontext/vrfcontext-33dfbcd7-867c-4e3e-acf7-96bf679d5a0d#global',
            'inline_health_monitor': True,
            'default_server_port': 8000,
            'request_queue_depth': 128,
            'graceful_disable_timeout': 1,
            'sni_enabled': True,
            'server_count': 3,
            'uuid': 'pool-09201181-747e-41ea-872d-e9a7df71b726',
            'request_queue_enabled': False,
            'name': 'p1',
            'max_concurrent_connections_per_server': 0,
            'url': 'https://192.0.2.42/api/pool/pool-09201181-747e-41ea-872d-e9a7df71b726#p1',
            'enabled': True,
            'connection_ramp_duration': 10}

        existing_obj = {
            'lb_algorithm': 'LB_ALGORITHM_ROUND_ROBIN',
            'use_service_port': False,
            'server_auto_scale': False,
            'host_check_enabled': False,
            'tenant_ref': 'https://192.0.2.42/api/tenant/admin',
            'capacity_estimation': False,
            'servers': [{
                'hostname': 'grastogi-server6', 'ratio': 1,
                'ip': {
                    'type': 'V4',
                    'addr': '198.51.100.62'
                },
                'discovered_networks': [{
                    'subnet': [{
                        'mask': 24,
                        'ip_addr': {
                            'type': 'V4',
                            'addr': '198.51.100.0'
                        }
                    }],
                    'network_ref': 'https://192.0.2.42/api/network/dvportgroup-53975-10.10.2.10'
                }],
                'enabled': True,
                'nw_ref': 'https://192.0.2.42/api/vimgrnwruntime/dvportgroup-53975-10.10.2.10',
                'verify_network': False,
                'static': False,
                'resolve_server_by_dns': False,
                'external_uuid': 'vm-4230615e-bc0b-3d33-3929-1c7328575993',
                'vm_ref': 'https://192.0.2.42/api/vimgrvmruntime/vm-4230615e-bc0b-3d33-3929-1c7328575993'
            }, {
                'hostname': 'grastogi-server6',
                'ratio': 1,
                'ip': {
                    'type': 'V4',
                    'addr': '198.51.100.61'
                },
                'discovered_networks': [{
                    'subnet': [{
                        'mask': 24,
                        'ip_addr': {
                            'type': 'V4',
                            'addr': '198.51.100.0'
                        }
                    }],
                    'network_ref': 'https://192.0.2.42/api/network/dvportgroup-53975-10.10.2.10'
                }],
                'enabled': True,
                'nw_ref': 'https://192.0.2.42/api/vimgrnwruntime/dvportgroup-53975-10.10.2.10',
                'verify_network': False,
                'static': False,
                'resolve_server_by_dns': False,
                'external_uuid': 'vm-4230615e-bc0b-3d33-3929-1c7328575993',
                'vm_ref': 'https://192.0.2.42/api/vimgrvmruntime/vm-4230615e-bc0b-3d33-3929-1c7328575993'
            }, {
                'hostname': 'grastogi-server6',
                'ratio': 1,
                'ip': {
                    'type': 'V4',
                    'addr': '198.51.100.65'
                },
                'discovered_networks': [{
                    'subnet': [{
                        'mask': 24,
                        'ip_addr': {
                            'type': 'V4',
                            'addr': '198.51.100.0'
                        }
                    }],
                    'network_ref': 'https://192.0.2.42/api/network/dvportgroup-53975-10.10.2.10'
                }],
                'enabled': True,
                'nw_ref': 'https://192.0.2.42/api/vimgrnwruntime/dvportgroup-53975-10.10.2.10',
                'verify_network': False,
                'static': False,
                'resolve_server_by_dns': False,
                'external_uuid': 'vm-4230615e-bc0b-3d33-3929-1c7328575993',
                'vm_ref': 'https://192.0.2.42/api/vimgrvmruntime/vm-4230615e-bc0b-3d33-3929-1c7328575993'
            }],
            'fewest_tasks_feedback_delay': 10,
            'cloud_ref': 'https://192.0.2.42/api/cloud/cloud-e0696a58-8b72-4026-923c-9a87c38a2489',
            'vrf_ref': 'https://192.0.2.42/api/vrfcontext/vrfcontext-33dfbcd7-867c-4e3e-acf7-96bf679d5a0d',
            'inline_health_monitor': True,
            'default_server_port': 8000,
            'request_queue_depth': 128,
            'graceful_disable_timeout': 1,
            'sni_enabled': True,
            'server_count': 3,
            'uuid': 'pool-09201181-747e-41ea-872d-e9a7df71b726',
            'request_queue_enabled': False,
            'name': 'p1',
            'max_concurrent_connections_per_server': 0,
            'url': 'https://192.0.2.42/api/pool/pool-09201181-747e-41ea-872d-e9a7df71b726',
            'enabled': True,
            'connection_ramp_duration': 10
        }

        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

    def testAWSVs(self):
        existing_obj = {
            'network_profile_ref': 'https://12.97.16.202/api/networkprofile/networkprofile-9a0a9896-6876-44c8-a3ee-512a968905f2#System-TCP-Proxy',
            'port_uuid': 'eni-4144e73c',
            'weight': 1,
            'availability_zone': 'us-west-2a',
            'enabled': True,
            'flow_dist': 'LOAD_AWARE',
            'subnet_uuid': 'subnet-91f0b6f4',
            'delay_fairness': False,
            'avi_allocated_vip': True,
            'vrf_context_ref': 'https://12.97.16.202/api/vrfcontext/vrfcontext-722b280d-b555-4d82-9b35-af9442c0cb86#global',
            'subnet': {
                'ip_addr': {
                    'type': 'V4',
                    'addr': '198.51.100.0'
                },
                'mask': 24
            },
            'cloud_type': 'CLOUD_AWS', 'uuid': 'virtualservice-a5f49b99-22c8-42e6-aa65-3ca5f1e36b9e',
            'network_ref': 'https://12.97.16.202/api/network/subnet-91f0b6f4',
            'cloud_ref': 'https://12.97.16.202/api/cloud/cloud-49829414-c704-43ca-9dff-05b9e8474dcb#AWS Cloud',
            'avi_allocated_fip': False,
            'se_group_ref': 'https://12.97.16.202/api/serviceenginegroup/serviceenginegroup-3bef6320-5a2d-4801-85c4-ef4f9841f235#Default-Group',
            'scaleout_ecmp': False,
            'max_cps_per_client': 0,
            'type': 'VS_TYPE_NORMAL',
            'analytics_profile_ref': 'https://12.97.16.202/api/analyticsprofile/analyticsprofile-70f8b06f-7b6a-4500-b829-c869bbca2009#System-Analytics-Profile',
            'use_bridge_ip_as_vip': False,
            'application_profile_ref': 'https://12.97.16.202/api/applicationprofile/applicationprofile-103cbc31-cac5-46ab-8e66-bbbb2c8f551f#System-HTTP',
            'auto_allocate_floating_ip': False,
            'services': [{
                'enable_ssl': False,
                'port_range_end': 80,
                'port': 80
            }],
            'active_standby_se_tag': 'ACTIVE_STANDBY_SE_1',
            'ip_address': {
                'type': 'V4',
                'addr': '198.51.100.33'
            },
            'ign_pool_net_reach': False,
            'east_west_placement': False,
            'limit_doser': False,
            'name': 'wwwawssit.ebiz.verizon.com',
            'url': 'https://12.97.16.202/api/virtualservice/virtualservice-a5f49b99-22c8-42e6-aa65-3ca5f1e36b9e#wwwawssit.ebiz.verizon.com',
            'ssl_sess_cache_avg_size': 1024,
            'enable_autogw': True,
            'auto_allocate_ip': True,
            'tenant_ref': 'https://12.97.16.202/api/tenant/tenant-f52f7a3e-6876-4bb9-b8f7-3cab636dadf2#Sales',
            'remove_listening_port_on_vs_down': False
        }
        obj = {'auto_allocate_ip': True, 'subnet_uuid': 'subnet-91f0b6f4', 'cloud_ref': '/api/cloud?name=AWS Cloud', 'services': [{'port': 80}],
               'name': 'wwwawssit.ebiz.verizon.com'}

        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

    def testhttppolicy(self):
        existing_obj = {
            "http_request_policy": {
                "rules": [{
                    "enable": True,
                    "index": 0,
                    "match": {
                        "path": {
                            "match_case": "INSENSITIVE",
                            "match_criteria": "CONTAINS",
                            "match_str": ["xvz", "rst"]
                        }
                    },
                    "name": "blah",
                    "switching_action": {
                        "action": "HTTP_SWITCHING_SELECT_POOL",
                        "pool_ref": "https://12.97.16.202/api/pool/pool-d7f6f5e7-bd26-49ad-aeed-965719eb140b#abc",
                        "status_code": "HTTP_LOCAL_RESPONSE_STATUS_CODE_200"
                    }
                }]
            },
            "is_internal_policy": False,
            "name": "blah",
            "tenant_ref": "https://12.97.16.202/api/tenant/tenant-f52f7a3e-6876-4bb9-b8f7-3cab636dadf2#Sales",
            "url": "https://12.97.16.202/api/httppolicyset/httppolicyset-ffd8354b-671b-48d5-92cc-69a9057aad0c#blah",
            "uuid": "httppolicyset-ffd8354b-671b-48d5-92cc-69a9057aad0c"
        }

        obj = {
            "http_request_policy": {
                "rules": [{
                    "enable": True,
                    "index": "0",
                    "match": {
                        "path": {
                            "match_case": "INSENSITIVE",
                            "match_criteria": "CONTAINS",
                            "match_str": ["xvz", "rst"]
                        }
                    },
                    "name": "blah",
                    "switching_action": {
                        "action": "HTTP_SWITCHING_SELECT_POOL",
                        "pool_ref": "/api/pool?name=abc",
                        "status_code": "HTTP_LOCAL_RESPONSE_STATUS_CODE_200"
                    }
                }]
            },
            "is_internal_policy": False,
            "tenant": "Sales"
        }
        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

    def testCleanupFields(self):
        obj = {'name': 'testpool',
               'scalar_field': {'state': 'absent'},
               'list_fields': [{'x': '1'}, {'y': {'state': 'absent'}}]}

        cleanup_absent_fields(obj)
        assert 'scalar_field' not in obj
        for elem in obj['list_fields']:
            assert 'y' not in elem

    def testGSLB(self):
        obj = {
            'domain_names': ['cloud5.avi.com', 'cloud6.avi.com'],
            'health_monitor_scope': 'GSLB_SERVICE_HEALTH_MONITOR_ALL_MEMBERS',
            'groups': [{
                'priority': 20,
                'members': [{
                    'ip': {
                        'type': 'V4',
                        'addr': '198.51.100.1'
                    },
                    'enabled': True, 'ratio': 1
                }, {
                    'ip': {
                        'type': 'V4',
                        'addr': '198.51.100.10'
                    },
                    'enabled': True,
                    'ratio': 1
                }],
                'algorithm': 'GSLB_ALGORITHM_CONSISTENT_HASH',
                'name': 'sc'
            }, {
                'priority': 14,
                'members': [{
                    'ip': {
                        'type': 'V4',
                        'addr': '198.51.100.2'
                    },
                    'enabled': True,
                    'ratio': 1
                }],
                'algorithm': 'GSLB_ALGORITHM_ROUND_ROBIN',
                'name': 'cn'
            }, {
                'priority': 15,
                'members': [{
                    'ip': {
                        'type': 'V4',
                        'addr': '198.51.100.3'
                    },
                    'enabled': True, 'ratio': 1
                }],
                'algorithm': 'GSLB_ALGORITHM_ROUND_ROBIN',
                'name': 'in'
            }],
            'name': 'gs-3',
            'num_dns_ip': 2
        }
        existing_obj = {
            u'controller_health_status_enabled': True,
            u'uuid': u'gslbservice-ab9b36bd-3e95-4c2e-80f8-92905c2eccb2',
            u'wildcard_match': False,
            u'url': u'https://192.0.2.42/api/gslbservice/gslbservice-ab9b36bd-3e95-4c2e-80f8-92905c2eccb2#gs-3',
            u'tenant_ref': u'https://192.0.2.42/api/tenant/admin#admin',
            u'enabled': True,
            u'domain_names': [u'cloud5.avi.com', u'cloud6.avi.com'],
            u'use_edns_client_subnet': True,
            u'groups': [{
                u'priority': 20,
                u'members': [{
                    u'ip': {
                        u'type': u'V4',
                        u'addr': u'198.51.100.1'
                    },
                    u'ratio': 1,
                    u'enabled': True
                }, {
                    u'ip': {
                        u'type': u'V4',
                        u'addr': u'198.51.100.10'
                    },
                    u'ratio': 1,
                    u'enabled': True
                }],
                u'name': u'sc',
                u'algorithm': u'GSLB_ALGORITHM_CONSISTENT_HASH'
            }, {
                u'priority': 14,
                u'members': [{
                    u'ip': {
                        u'type': u'V4',
                        u'addr': u'198.51.100.2'
                    },
                    u'ratio': 1,
                    u'enabled': True
                }],
                u'name': u'cn',
                u'algorithm': u'GSLB_ALGORITHM_ROUND_ROBIN'
            }, {
                u'priority': 15,
                u'members': [{
                    u'ip': {
                        u'type': u'V4',
                        u'addr': u'198.51.100.3'
                    },
                    u'ratio': 1,
                    u'enabled': True
                }],
                u'name': u'in',
                u'algorithm': u'GSLB_ALGORITHM_ROUND_ROBIN'
            }],
            u'num_dns_ip': 2,
            u'health_monitor_scope': u'GSLB_SERVICE_HEALTH_MONITOR_ALL_MEMBERS',
            u'name': u'gs-3'
        }
        diff = avi_obj_cmp(obj, existing_obj)
        assert diff

    def testNoneParams(self):
        objwnone = {
            'name': 'testpool',
            'scalar_field': None,
            'list_fields': {
                'y': None,
                'z': 'zz'
            }
        }
        obj = {
            'name': 'testpool',
            'list_fields': {
                'z': 'zz'
            }
        }

        result = avi_obj_cmp(objwnone, obj)
        assert result
